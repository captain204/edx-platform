from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'courseware.tests.test_footer')

from lms.djangoapps.courseware.tests.test_footer import *
