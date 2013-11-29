#!/usr/bin/env python

import unittest
import graphitesend


class TestAll(unittest.TestCase):
    """ Basic tests ( better than nothing ) """

    def setUp(self):
        """ reset graphitesend """
        # Drop any connections or modules that have been setup from other tests
        graphitesend.reset()
        # Monkeypatch the graphitesend so that it points at a graphite service
        # running on one of my (dannyla@linux.com) systems.
        # graphitesend.default_graphite_server = 'graphite.dansysadm.com'
        graphitesend.default_graphite_server = 'localhost'
        import os
        self.hostname = os.uname()[1]

    def tearDown(self):
        """ reset graphitesend """
        # Drop any connections or modules that have been setup from other tests
        graphitesend.reset()

    def test_connect_exception_on_badhost(self):
        bad_graphite_server = 'missinggraphiteserver.example.com'
        graphitesend.default_graphite_server = bad_graphite_server
        with self.assertRaises(graphitesend.GraphiteSendException):
            graphitesend.init()

    def test_set_lowercase_metric_names(self):
        g = graphitesend.init(lowercase_metric_names=True)
        self.assertEqual(g.lowercase_metric_names, True)

    def test_lowercase_metric_names(self):
        g = graphitesend.init(lowercase_metric_names=True)
        send_data = g.send('METRIC', 1)
        self.assertEqual('metric' in send_data, True)
        self.assertEqual('METRIC' in send_data, False)

    def test_create_graphitesend_instance(self):
        g = graphitesend.init()
        expected_type = type(graphitesend.GraphiteClient())
        g_type = type(g)
        self.assertEqual(g_type, expected_type)

    def test_monkey_patch_of_graphitehost(self):
        g = graphitesend.init()
        custom_prefix = g.addr[0]
        self.assertEqual(custom_prefix, 'localhost')

    def test_noprefix(self):
        g = graphitesend.init()
        custom_prefix = g.prefix
        self.assertEqual(custom_prefix, 'systems.%s.' % self.hostname)

    def test_system_name(self):
        g = graphitesend.init(system_name='remote_host')
        custom_prefix = g.prefix
        self.assertEqual(custom_prefix, 'systems.remote_host.')

    def test_prefix(self):
        g = graphitesend.init(prefix='custom_prefix')
        custom_prefix = g.prefix
        self.assertEqual(custom_prefix, 'custom_prefix.')

    def test_prefix_double_dot(self):
        g = graphitesend.init(prefix='custom_prefix.')
        custom_prefix = g.prefix
        self.assertEqual(custom_prefix, 'custom_prefix.')

    def test_prefix_remove_spaces(self):
        g = graphitesend.init(prefix='custom prefix')
        custom_prefix = g.prefix
        self.assertEqual(custom_prefix, 'custom_prefix.')

    def test_set_prefix_group(self):
        g = graphitesend.init(prefix='prefix', group='group')
        custom_prefix = g.prefix
        self.assertEqual(custom_prefix, 'prefix.%s.group.' % self.hostname)

    def test_set_prefix_group_system(self):
        g = graphitesend.init(prefix='prefix', system_name='system', group='group')
        custom_prefix = g.prefix
        self.assertEqual(custom_prefix, 'prefix.system.group.')

    def test_set_suffix(self):
        g = graphitesend.init(suffix='custom_suffix')
        custom_suffix = g.suffix
        self.assertEqual(custom_suffix, 'custom_suffix')

    def test_set_group_prefix(self):
        g = graphitesend.init(group='custom_group')
        expected_prefix = "systems.%s.custom_group" % self.hostname
        custom_prefix = g.prefix
        self.assertEqual(custom_prefix, expected_prefix)

    def test_default_prefix(self):
        g = graphitesend.init()
        expected_prefix = "systems.%s." % self.hostname
        custom_prefix = g.prefix
        self.assertEqual(custom_prefix, expected_prefix)

    def test_leave_suffix(self):
        g = graphitesend.init()
        default_suffix = g.suffix
        self.assertEqual(default_suffix, '')

    def test_clean_metric(self):
        g = graphitesend.init()
        #
        metric_name = g.clean_metric_name('test(name)')
        self.assertEqual(metric_name, 'test_name')
        #
        metric_name = g.clean_metric_name('test name')
        self.assertEqual(metric_name, 'test_name')
        #
        metric_name = g.clean_metric_name('test  name')
        self.assertEqual(metric_name, 'test__name')

    def test_reset(self):
        graphitesend.init()
        graphitesend.reset()
        graphite_instance = graphitesend._module_instance
        self.assertEqual(graphite_instance, None)

    def test_force_failure_on_send(self):
        graphite_instance = graphitesend.init()
        graphite_instance.disconnect()
        with self.assertRaises(graphitesend.GraphiteSendException):
            graphite_instance.send('metric', 0)

    def test_force_unknown_failure_on_send(self):
        graphite_instance = graphitesend.init()
        graphite_instance.socket = None
        with self.assertRaises(graphitesend.GraphiteSendException):
            graphite_instance.send('metric', 0)

    def test_send_list_metric_value(self):
        graphite_instance = graphitesend.init(prefix='test')
        response = graphite_instance.send_list([('metric', 1)])
        self.assertEqual('sent 32 long message: test.metric' in response, True)
        self.assertEqual('1.00000' in response, True)

    def test_send_list_metric_value_single_timestamp(self):
        # Make sure it can handle custom timestamp
        graphite_instance = graphitesend.init(prefix='test')
        response = graphite_instance.send_list([('metric', 1)], timestamp=1)
        # self.assertEqual('sent 23 long message: test.metric' in response,
        # True)
        self.assertEqual('1.00000' in response, True)
        self.assertEqual(response.endswith('1\n'), True)

    def test_send_list_metric_value_timestamp(self):
        graphite_instance = graphitesend.init(prefix='test')

        # Make sure it can handle custom timestamp
        response = graphite_instance.send_list([('metric', 1, 1)])
        # self.assertEqual('sent 23 long message: test.metric' in response,
        # True)
        self.assertEqual('1.00000' in response, True)
        self.assertEqual(response.endswith('1\n'), True)

    def test_send_list_metric_value_timestamp_2(self):
        graphite_instance = graphitesend.init(prefix='test')
        # Make sure it can handle custom timestamp
        response = graphite_instance.send_list(
            [('metric', 1, 1), ('metric', 1, 2)])
        # self.assertEqual('sent 46 long message:' in response, True)
        self.assertEqual('test.metric 1.000000 1' in response, True)
        self.assertEqual('test.metric 1.000000 2' in response, True)

    def test_send_list_metric_value_timestamp_3(self):
        graphite_instance = graphitesend.init(prefix='test')
        # Make sure it can handle custom timestamp, fill in the missing with
        # the current time.
        response = graphite_instance.send_list(
            [
                ('metric', 1, 1),
                ('metric', 2),
            ]
        )

        # self.assertEqual('sent 46 long message:' in response, True)
        self.assertEqual('test.metric 1.000000 1' in response, True)
        self.assertEqual('test.metric 2.000000 2' not in response, True)

    def test_send_list_metric_value_timestamp_default(self):
        graphite_instance = graphitesend.init(prefix='test')
        # Make sure it can handle custom timestamp, fill in the missing with
        # the current time.
        response = graphite_instance.send_list(
            [
                ('metric', 1, 1),
                ('metric', 2),
            ],
            timestamp='4'
        )
        # self.assertEqual('sent 69 long message:' in response, True)
        self.assertEqual('test.metric 1.000000 1' in response, True)
        self.assertEqual('test.metric 2.000000 4' in response, True)

    def test_send_list_metric_value_timestamp_default_2(self):
        graphite_instance = graphitesend.init(prefix='test')
        # Make sure it can handle custom timestamp, fill in the missing with
        # the current time.
        response = graphite_instance.send_list(
            [
                ('metric', 1),
                ('metric', 2, 2),
            ],
            timestamp='4'
        )
        # self.assertEqual('sent 69 long message:' in response, True)
        self.assertEqual('test.metric 1.000000 4' in response, True)
        self.assertEqual('test.metric 2.000000 2' in response, True)


if __name__ == '__main__':
    unittest.main()
