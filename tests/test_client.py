import sys

from bugsnag import Client, Configuration
from tests.utils import IntegrationTest



class ClientTest(IntegrationTest):
    def setUp(self):
        super(ClientTest, self).setUp()

        self.client = Client(api_key='testing client key',
                             use_ssl=False, endpoint=self.server.address,
                             asynchronous=False,
                             install_sys_hook=False)

    # Initialisation

    def test_init_no_configuration(self):
        client = Client(install_sys_hook=False)
        self.assertTrue(isinstance(client.configuration, Configuration))

    def test_init_configuration(self):
        configuration = Configuration()
        client = Client(configuration=configuration, install_sys_hook=False)

        self.assertEqual(client.configuration, configuration)

    def test_init_options(self):
        client = Client(api_key='testing client key', install_sys_hook=False)
        self.assertEqual(client.configuration.api_key, 'testing client key')

    # Sending Notification

    def test_notify_exception(self):
        self.client.notify(Exception('Testing Notify'))

        self.assertEqual(len(self.server.received), 1)

    def test_notify_exc_info(self):
        try:
            raise Exception('Testing Notify EXC Info')
        except Exception:
            self.client.notify_exc_info(*sys.exc_info())

        self.assertEqual(len(self.server.received), 1)

    # Context

    def test_notify_context(self):
        with self.client.context():
            raise Exception('Testing Notify Context')

        self.assertEqual(len(self.server.received), 1)

    def test_notify_context_swallow(self):
        with self.assertRaises(Exception):
            with self.client.context(swallow=False):
                raise Exception('Testing Notify Context')

        self.assertEqual(len(self.server.received), 1)

    def test_notify_context_options(self):
        with self.client.context(section={'key':'value'}):
            raise Exception('Testing Notify Context')

        self.assertEqual(len(self.server.received), 1)
        json_body = self.server.received[0]['json_body']
        event = json_body['events'][0]
        self.assertEqual(event['metaData']['section'], {
            'key': 'value'
        })

    def test_no_exception_context(self):
        with self.client.context():
            pass

        self.assertEqual(len(self.server.received), 0)

    # Exception Hook

    def test_exception_hook(self):
        try:
            raise Exception('Testing excepthook notify')
        except Exception:
            self.client.excepthook(*sys.exc_info())

        self.assertEqual(len(self.server.received), 1)
        event = self.server.received[0]['json_body']['events'][0]
        self.assertEqual(event['severity'], 'error')

    def test_exception_hook_disabled(self):
        self.client.configuration.auto_notify = False

        try:
            raise Exception('Testing excepthook notify')
        except Exception:
            self.client.excepthook(*sys.exc_info())

        self.assertEqual(len(self.server.received), 0)

    def test_installed_except_hook(self):
        client = Client()

        # Prevent the existing hook from being called
        client.sys_excepthook = None

        self.hooked = None
        def hooked_except_hook(*exc_info):
            self.hooked = exc_info

        client.excepthook = hooked_except_hook

        try:
            raise Exception('Testing excepthook notify')
        except Exception:
            sys.excepthook(*sys.exc_info())

        self.assertEqual(self.hooked[0], Exception)

    def test_installed_except_hook_calls_previous_except_hook(self):
        self.hook_ran = False
        def excepthook(*exc_info):
            self.hook_ran = True
        sys.excepthook = excepthook

        client = Client(auto_notify=False)

        try:
            raise Exception('Testing excepthook notify')
        except Exception:
            sys.excepthook(*sys.exc_info())

        self.assertTrue(self.hook_ran)

    def test_unregister_installed_except_hook(self):
        # Setup an original except hook
        def excepthook(*exc_info):
            pass
        sys.excepthook = excepthook

        client = Client()
        self.assertNotEqual(sys.excepthook, excepthook)
        client.uninstall_sys_hook()
        self.assertEqual(sys.excepthook, excepthook)
