# -*- coding: utf-8 -*-
"""
Test the bulk email opt out view.
"""

import ddt
from django.http import Http404
from django.test.client import RequestFactory
from django.test.utils import override_settings
from django.urls import reverse

from bulk_email.models import Optout
from bulk_email.views import opt_out_email_updates
from six import text_type

from lms.djangoapps.discussion.notification_prefs.views import UsernameCipher
from openedx.core.lib.tests import attr
from student.tests.factories import UserFactory
from xmodule.modulestore.tests.factories import CourseFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase


@attr(shard=1)
@ddt.ddt
@override_settings(SECRET_KEY="test secret key")
class OptOutEmailUpdatesViewTest(ModuleStoreTestCase):
    """
    Check the opt out email functionality.
    """
    def setUp(self):
        super(OptOutEmailUpdatesViewTest, self).setUp()
        self.user = UserFactory.create(username="testuser1", email='test@example.com')
        self.course = CourseFactory.create(run='testcourse1', display_name='Test Course Title')
        self.token = UsernameCipher.encrypt('testuser1')
        self.request_factory = RequestFactory()
        self.url = reverse('bulk_email_opt_out', args=[self.token, text_type(self.course.id)])

        # Ensure we start with no opt-out records
        self.assertEqual(Optout.objects.count(), 0)

    def test_opt_out_email_confirm(self):
        """
        Ensure that the default GET view asks for confirmation.
        """
        response = self.client.get(self.url)
        self.assertContains(response, "confirm unsubscribe from")
        self.assertEqual(Optout.objects.count(), 0)

    def test_opt_out_email_unsubscribe(self):
        """
        Ensure that the POSTing "confirm" creates the opt-out record.
        """
        response = self.client.post(self.url, {'unsubscribe': True})
        self.assertContains(response, "You have successfully unsubscribed from")
        self.assertEqual(Optout.objects.count(), 1)

    def test_opt_out_email_cancel(self):
        """
        Ensure that the POSTing "cancel" does not create the opt-out record
        """
        response = self.client.post(self.url)
        self.assertContains(response, "You have not been unsubscribed from")
        self.assertEqual(Optout.objects.count(), 0)

    @ddt.data(
        ("ZOMG INVALID BASE64 CHARS!!!", "base64url", False),
        ("Non-ASCII\xff".encode(), "base64url", False),
        ("D6L8Q01ztywqnr3coMOlq0C3DG05686lXX_1ArEd0ok", "base64url", False),
        ("AAAAAAAAAAA=", "initialization_vector", False),
        ("nMXVK7PdSlKPOovci-M7iqS09Ux8VoCNDJixLBmj", "aes", False),
        ("AAAAAAAAAAAAAAAAAAAAAMoazRI7ePLjEWXN1N7keLw=", "padding", False),
        ("AAAAAAAAAAAAAAAAAAAAACpyUxTGIrUjnpuUsNi7mAY=", "username", False),
        ("_KHGdCAUIToc4iaRGy7K57mNZiiXxO61qfKT08ExlY8=", "course", 'course-v1:testcourse'),
    )
    @ddt.unpack
    def test_unsubscribe_invalid_token(self, token, message, course):
        """
        Make sure that view returns 404 in case token is not valid
        """
        request = self.request_factory.get("dummy")
        with self.assertRaises(Http404) as err:
            opt_out_email_updates(request, token, course)
            self.assertIn(message, err)
