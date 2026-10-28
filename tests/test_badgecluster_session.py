"""Foreground orchestration, loss/retry, timeout, pause and exit behavior."""
import importlib.util
from pathlib import Path
import unittest
import test_badgecluster as base

spec = importlib.util.spec_from_file_location('cluster_session', base.APP / 'cluster_session.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class Transport:
    def __init__(self):
        self.requests = []
        self.result = None
        self.cancels = 0

    def start(self, request):
        self.requests.append(request)

    def poll(self):
        result, self.result = self.result, None
        return result

    def cancel(self):
        self.cancels += 1


class SessionTests(unittest.TestCase):
    def setUp(self):
        self.now = 0
        self.worker = base.core.Worker(0, base.add, base.diff, lambda: 0.5, lambda: self.now)
        self.client = base.core.Contributions('node-test', 'session-test', 0, base.add, base.diff)
        self.transport = Transport()
        self.session = module.Session(self.worker, self.client, self.transport)

    def start_request(self):
        self.now = 60000
        self.client.next_sync = self.now
        for _ in range(10):
            self.session.step(self.now)
        self.assertTrue(self.session.inflight)
        self.assertEqual(self.worker.samples, 250)

    def response(self):
        pending = self.client.pending
        return dict(acceptedSequence=pending['sequence'], acceptedSamples=pending['samples'],
                    cluster=dict(samples=pending['samples'], inside=pending['inside'], activeNodes=1))

    def test_waits_for_batch_to_finish_and_for_server_ack(self):
        self.start_request()
        self.assertEqual(self.client.accepted_samples, 0)
        self.assertEqual(self.session.status(), 'CONNECTING')
        self.transport.result = ('ok', self.response())
        self.session.step(self.now)
        self.assertEqual(self.client.accepted_samples, 250)
        self.assertEqual(self.session.status(), 'CONTRIBUTING')

    def test_response_loss_retries_the_same_snapshot_with_backoff(self):
        self.start_request()
        original = dict(self.transport.requests[-1])
        self.transport.result = ('error', None)
        self.session.step(self.now)
        self.assertTrue(self.client.offline)
        self.assertEqual(self.client.next_sync, 90000)
        self.now = 90000
        self.session.step(self.now)
        self.assertEqual(self.transport.requests[-1], original)
        self.transport.result = ('ok', self.response())
        self.session.step(self.now)
        self.assertEqual(self.client.accepted_samples, 250)
        self.assertEqual(self.client.failures, 0)

    def test_bounded_timeout_keeps_snapshot_and_cancels_transport(self):
        self.start_request()
        self.now += 5000
        self.session.step(self.now)
        self.assertFalse(self.session.inflight)
        self.assertEqual(self.session.error, 'timeout')
        self.assertEqual(self.transport.cancels, 1)
        self.assertEqual(self.client.pending['samples'], 250)
        self.assertEqual(self.client.accepted_samples, 0)

    def test_compute_continues_while_transport_is_pending(self):
        self.start_request()
        self.worker.next_batch = self.now
        self.session.step(self.now)
        self.assertEqual(self.worker.samples, 275)
        self.assertEqual(self.client.pending['samples'], 250)

    def test_close_during_request_stops_compute_and_all_future_sends(self):
        self.start_request()
        self.session.close()
        self.session.step(240000)
        self.assertEqual(self.worker.samples, 250)
        self.assertEqual(len(self.transport.requests), 1)
        self.assertEqual(self.transport.cancels, 1)
        self.assertEqual(self.session.status(), 'STOPPING')

    def test_low_battery_cancels_request_and_prevents_new_sends(self):
        self.start_request()
        self.worker.power(19)
        self.session.step(self.now)
        self.session.step(240000)
        self.assertEqual(len(self.transport.requests), 1)
        self.assertFalse(self.session.inflight)
        self.assertEqual(self.session.status(), 'PAUSED')

    def test_bad_ack_does_not_accept_local_work_or_crash(self):
        self.start_request()
        response = self.response()
        response['acceptedSamples'] = True
        self.transport.result = ('ok', response)
        self.session.step(self.now)
        self.assertEqual(self.client.accepted_samples, 0)
        self.assertEqual(self.session.error, 'invalid_response')
        self.assertEqual(self.session.status(), 'OFFLINE')

    def test_no_transport_is_offline_and_never_attempts_network(self):
        session = module.Session(self.worker, self.client)
        self.now = 120000
        for _ in range(10):
            session.step(self.now)
        self.assertEqual(self.worker.samples, 250)
        self.assertEqual(self.client.sequence, 0)
        self.assertEqual(session.status(), 'OFFLINE')

    def test_timeout_and_retry_across_ticks_wrap(self):
        self.now = base.WRAP - 1000
        self.worker.next_batch = base.add(self.now, 60000)
        self.client.next_sync = self.now
        self.session.step(self.now)
        self.assertTrue(self.session.inflight)
        self.now = base.add(self.now, 5000)
        self.session.step(self.now)
        self.assertEqual(self.session.error, 'timeout')
        self.assertEqual(self.client.next_sync, base.add(self.now, 30000))

    def test_wrong_global_inside_count_is_rejected(self):
        self.start_request()
        response = self.response()
        response['cluster']['inside'] = 0
        self.transport.result = ('ok', response)
        self.session.step(self.now)
        self.assertTrue(self.client.offline)
        self.assertEqual(self.client.accepted_samples, 0)


if __name__ == '__main__':
    unittest.main()
