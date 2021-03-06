"""
Runs tests for the studio views.
"""
from ddt import ddt, unpack, data
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.wait import WebDriverWait
from base_test import PollBaseTest
from studio_scenarios import ddt_scenarios


@ddt
class StudioTest(PollBaseTest):
    """
    Mixin class for poll studio tests.
    """
    default_css_selector = '#settings-tab'

    def studio_save(self):
        self.browser.find_element_by_css_selector('#poll-submit-options').click()

    @data(*ddt_scenarios)
    @unpack
    def test_add_items(self, page_name, item_type, num_existing_items, answer_css_selector):
        """
        Verify we can add more than one item and they both save.
        """
        self.go_to_page(page_name, view_name='studio_view')
        add_item_button = self.browser.find_element_by_css_selector('#poll-add-%s' % item_type)
        # Add two answers
        add_item_button.click()
        add_item_button.click()
        # Make sure we get forms for both.
        wait = WebDriverWait(self.browser, self.timeout)
        selector = '.poll-%s-studio-item' % item_type
        total = num_existing_items + 2

        def get_last_item(driver):
            items = driver.find_elements_by_css_selector(selector)
            try:
                # Start from 0
                return items[total - 1]
            except IndexError:
                raise NoSuchElementException

        wait.until(get_last_item, u"{}th copy of selector '{}' should exist.".format(total, selector))

        answers = self.browser.find_elements_by_css_selector('.poll-%s-studio-item' % item_type)
        results = []
        for index, element in enumerate(answers[-2:]):
            # First input is the label, which should always be there.
            label = element.find_element_by_css_selector('input')
            text = 'Test %s %s' % (item_type, index)
            label.send_keys(text)
            results.append(text)

        self.studio_save()
        self.go_to_page(page_name, css_selector='div.poll-block')
        answers = [element.text for element in self.browser.find_elements_by_css_selector(answer_css_selector)]
        self.assertEqual(answers[-2:], results)

