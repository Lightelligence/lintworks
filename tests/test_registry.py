"""Test connectivity of Broadcasters and Listeners.

Ensures that the automatic registration of Listeners to appropriate
Broadcasters occurs.

"""
import unittest
from mock import MagicMock
from collections import defaultdict

from context import lintworks
from lintworks import base

# pylint: disable=too-few-public-methods,missing-docstring,unused-variable

class SubscriptionsTestCase(unittest.TestCase):
    """Check that Broadcasters and Subscribers actually link together."""

    def setUp(self):
        # Reset the registry between tests
        base.Broadcaster.listener_registry = defaultdict(list)

    def test_simple(self):
        """Create a single Broadcaster and subscribed Listener.

        Ensure they are connected and the appropriate update function is called.

        """
        class TestBroadcaster(base.Broadcaster):
            pass

        class TestListener(base.Listener):
            subscribe_to = [TestBroadcaster]

        self.assertIn(TestListener, TestBroadcaster.listener_registry[TestBroadcaster])

        tbc = TestBroadcaster(gc=None, parent=None)
        self.assertEqual(len(tbc.listener_instances), 1)

        created_listener = tbc.listener_instances[0]
        self.assertTrue(isinstance(created_listener, TestListener))

        created_listener.update_test = MagicMock()
        tbc.broadcast(1, "a line of text")
        created_listener.update_test.assert_called_with(1, "a line of text")

    def test_cascade(self):
        """Test multiple levels of Broadcasters and Listeners.

        Make sure that the filtering Broacaster/Listener combos get created
        correctly.

        """
        class Tier0Broadcaster(base.Broadcaster):
            pass

        class Tier0Listener(base.Listener):
            subscribe_to = [Tier0Broadcaster]

        class Tier1Broadcaster(base.Broadcaster, base.Listener):
            subscribe_to = [Tier0Broadcaster]

            def update_tier0(self, *args):
                # Multiply by 2 to change values rather than doing filtering
                argsx2 = [x*2 for x in args]
                self.broadcast(*argsx2)

        class Tier1Listener(base.Listener):
            subscribe_to = [Tier1Broadcaster]

        class Tier01Listener(base.Listener):
            """Subscribes to both tier0 and tier1."""
            subscribe_to = [Tier0Broadcaster, Tier1Broadcaster]

        tier0_args = [1, 2, 3]
        tier1_args = [x*2 for x in tier0_args]

        t0_bc = Tier0Broadcaster(gc=None, parent=None)

        # Implicit ordering via order of registration
        t0_li, t1_bc, t01_li = t0_bc.listener_instances
        t1_li, t01_li_handle = t1_bc.listener_instances

        self.assertIs(t01_li, t01_li_handle)

        t0_li.update_tier0 = MagicMock()
        t1_li.update_tier1 = MagicMock()
        t01_li.update_tier0 = MagicMock()
        t01_li.update_tier1 = MagicMock()
        
        t0_bc.broadcast(*tier0_args)

        t01_li.update_tier0.assert_called_with(*tier0_args)
        t01_li.update_tier1.assert_called_with(*tier1_args)

        # Check ignore
        t01_li.update_tier0 = MagicMock() # Not sure how to reset these, so just creating new ones
        t01_li.update_tier1 = MagicMock()

        t01_li._ignore(Tier0Broadcaster)
        t0_bc.broadcast(*tier0_args)
        t01_li._pay_attention_to(Tier0Broadcaster)

        t01_li.update_tier0.assert_not_called()
        t01_li.update_tier1.assert_called_with(*tier1_args)

    @unittest.skip("Doesn't work when only inheriting from Broadcaster")
    def test_bad_broadcaster_name(self):

        """Create a Broadcaster with an illegal name.

        This naming convention is strictly enforced for consistency purposes
        (the Broadcaster's update function is derived from its name).

        """
        def create_bad_broadcaster():
            class MyBadBC(base.Broadcaster):
                pass

        self.assertRaisesRegexp(base.IllegalBroadcasterError,
                                "Broadcaster classes must end name",
                                create_bad_broadcaster)

    def test_bad_broadcaster_lis_name(self):
        """Similar to test_bad_broadcaster_name.

        This test also inherits from Listener, which causes the check to occur.

        """
        def create_bad_broadcaster():
            class MyBadBC(base.Broadcaster, base.Listener):
                pass

        self.assertRaisesRegex(base.IllegalBroadcasterError,
                               "Broadcaster classes must end name",
                               create_bad_broadcaster)

    def test_no_subscribe_to_set(self):
        """Ensures assertion fires if a user forgets to set subscribe_to."""
        class TestBroadcaster(base.Broadcaster):
            pass

        def create_bad_listener():
            class TestListener(base.Listener):
                pass

        self.assertRaisesRegex(base.IllegalListenerError,
                                "did not subscribe to any broadcasters",
                                create_bad_listener)

    def test_no_listeners(self):
        """Ensures assertion fires if there are no subscriptions."""
        def create_bad_listener():
            class TestListener(base.Listener):
                subscribe_to = []

        self.assertRaisesRegex(base.IllegalListenerError,
                                "did not subscribe to any broadcasters",
                                create_bad_listener)

    def test_not_a_broadcaster(self):
        """Throw error if a Listener subscribes to a non-Broadcaster."""
        def create_bad_listener():
            class TestListener(base.Listener):
                subscribe_to = [object]

        self.assertRaisesRegex(base.IllegalListenerError,
                                "is not a valid Broadcaster",
                                create_bad_listener)

    def test_subscribe_to_is_list(self):
        """Throw error subscribe_to varialbe is not a list."""
        class TestBroadcaster(base.Broadcaster):
            pass

        def create_bad_listener():
            class TestListener(base.Listener):
                subscribe_to = TestBroadcaster

        self.assertRaisesRegex(base.IllegalListenerError,
                                "subscribe_to variable must be of type list",
                                create_bad_listener)


    def test_missing_update_method(self):
        """Throw error if listener doesn't implement correct update method."""
        class TestBroadcaster(base.Broadcaster):
            pass

        class TestListener(base.Listener):
            subscribe_to = [TestBroadcaster]

        tb = TestBroadcaster(gc=None, parent=None)
        self.assertRaisesRegex(base.IllegalListenerError,
                               "subscribed to.*but does not have a update_test method.",
                               tb.broadcast)
        

if __name__ == '__main__':
    unittest.main()
