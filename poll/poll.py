"""TO-DO: Write a description of what this XBlock is."""
from collections import OrderedDict

from django.template import Template, Context

import pkg_resources

from xblock.core import XBlock
from xblock.fields import Scope, String, Dict, List
from xblock.fragment import Fragment
from xblockutils.resources import ResourceLoader

from .utils import process_markdown

# When changing these constants, check the templates as well for places
# where the user is informed about them.

MAX_PARAGRAPH_LEN = 5000

MAX_URL_LEN = 1000

MAX_ANSWER_LEN = 250

# These two don't have mentions in the templates, but will cause error
# messages.

MAX_ANSWERS = 25

MAX_KEY_LEN = 100


class PollBlock(XBlock):
    """
    Poll XBlock. Allows a teacher to poll users, and presents the results so
    far of the poll to the user when finished.
    """
    question = String(default='What is your favorite color?')
    # This will be converted into an OrderedDict.
    # Key, (Label, Image path)
    answers = List(
        default=(('R', {'label': 'Red', 'img': None}), ('B', {'label': 'Blue', 'img': None}),
                 ('G', {'label': 'Green', 'img': None}), ('O', {'label': 'Other', 'img': None})),
        scope=Scope.settings, help="The question on this poll."
    )
    feedback = String(default='', help="Text to display after the user votes.")
    tally = Dict(default={'R': 0, 'B': 0, 'G': 0, 'O': 0},
                 scope=Scope.user_state_summary,
                 help="Total tally of answers from students.")
    choice = String(scope=Scope.user_state, help="The student's answer")

    loader = ResourceLoader(__name__)

    def resource_string(self, path):
        """Handy helper for getting resources from our kit."""
        data = pkg_resources.resource_string(__name__, path)
        return data.decode("utf8")

    @XBlock.json_handler
    def get_results(self, data, suffix=''):
        detail, total = self.tally_detail()
        return {
            'question': process_markdown(self.question), 'tally': detail,
            'total': total, 'feedback': process_markdown(self.feedback),
        }

    def clean_tally(self):
        """
        Cleans the tally. Scoping prevents us from modifying this in the studio
        and in the LMS the way we want to without undesirable side effects. So
        we just clean it up on first access within the LMS, in case the studio
        has made changes to the answers.
        """
        answers = OrderedDict(self.answers)
        for key in answers.keys():
            if key not in self.tally:
                self.tally[key] = 0

        for key in self.tally.keys():
            if key not in answers:
                del self.tally[key]

    def any_image(self):
        """
        Find out if any answer has an image, since it affects layout.
        """
        return any(value['img'] for value in dict(self.answers).values())

    def tally_detail(self):
        """
        Tally all results.
        """
        tally = []
        answers = OrderedDict(self.answers)
        choice = self.get_choice()
        total = 0
        self.clean_tally()
        source_tally = self.tally
        any_img = self.any_image()
        for key, value in answers.items():
            count = int(source_tally[key])
            tally.append({
                'count': count,
                'answer': value['label'],
                'img': value['img'],
                'key': key,
                'top': False,
                'choice': False,
                'last': False,
                'any_img': any_img,
            })
            total += count

        for answer in tally:
            try:
                answer['percent'] = int(answer['count'] / float(total)) * 100
                if answer['key'] == choice:
                    answer['choice'] = True
            except ZeroDivisionError:
                answer['percent'] = 0

        tally.sort(key=lambda x: x['count'], reverse=True)
        # This should always be true, but on the off chance there are
        # no answers...
        if tally:
            # Mark the top item to make things easier for Handlebars.
            tally[0]['top'] = True
            tally[-1]['last'] = True
        return tally, total

    def get_choice(self):
        """
        It's possible for the choice to have been removed since
        the student answered the poll. We don't want to take away
        the user's progress, but they should be able to vote again.
        """
        if self.choice and self.choice in OrderedDict(self.answers):
            return self.choice
        else:
            return None

    def create_fragment(self, context, template, css, js, js_init):
        html = Template(
            self.resource_string(template)).render(Context(context))
        frag = Fragment(html)
        frag.add_javascript_url(
            self.runtime.local_resource_url(
                self, 'public/js/vendor/handlebars.js'))
        frag.add_css(self.resource_string(css))
        frag.add_javascript(self.resource_string(js))
        frag.initialize_js(js_init)
        return frag

    def student_view(self, context=None):
        """
        The primary view of the PollBlock, shown to students
        when viewing courses.
        """
        if not context:
            context = {}
        js_template = self.resource_string(
            '/public/handlebars/results.handlebars')

        choice = self.get_choice()

        context.update({
            'choice': choice,
            # Offset so choices will always be True.
            'answers': self.answers,
            'question': process_markdown(self.question),
            # Mustache is treating an empty string as true.
            'feedback': process_markdown(self.feedback) or False,
            'js_template': js_template,
            'any_img': self.any_image(),
            # The SDK doesn't set url_name.
            'url_name': getattr(self, 'url_name', ''),
        })

        if self.choice:
            detail, total = self.tally_detail()
            context.update({'tally': detail, 'total': total})

        return self.create_fragment(
            context, "public/html/poll.html", "public/css/poll.css",
            "public/js/poll.js", "PollBlock")

    @XBlock.json_handler
    def load_answers(self, data, suffix=''):
        return {
            'answers': [
                {
                    'key': key, 'text': value['label'], 'img': value['img']
                }
                for key, value in self.answers
            ]
        }

    def studio_view(self, context=None):
        if not context:
            context = {}

        js_template = self.resource_string('/public/handlebars/studio.handlebars')
        context.update({
            'question': self.question,
            'feedback': self.feedback,
            'js_template': js_template
        })
        return self.create_fragment(
            context, "public/html/poll_edit.html",
            "/public/css/poll_edit.css", "public/js/poll_edit.js", "PollEditBlock")

    @XBlock.json_handler
    def studio_submit(self, data, suffix=''):
        # I wonder if there's something for live validation feedback already.

        result = {'success': True, 'errors': []}
        question = data.get('question', '').strip()[:MAX_PARAGRAPH_LEN]
        feedback = data.get('feedback', '').strip()[:MAX_PARAGRAPH_LEN]
        if not question:
            result['errors'].append("You must specify a question.")
            result['success'] = False

        answers = []

        if 'answers' not in data or not isinstance(data['answers'], list):
            source_answers = []
            result['success'] = False
            result['errors'].append(
                "'answers' is not present, or not a JSON array.")
        else:
            source_answers = data['answers']

        # Set a reasonable limit to the number of answers in a poll.
        if len(source_answers) > MAX_ANSWERS:
            result['success'] = False
            result['errors'].append("")

        # Make sure all components are present and clean them.
        for answer in source_answers:
            if not isinstance(answer, dict):
                result['success'] = False
                result['errors'].append(
                    "Answer {0} not a javascript object!".format(answer))
                continue
            key = answer.get('key', '').strip()
            if not key:
                result['success'] = False
                result['errors'].append(
                    "Answer {0} contains no key.".format(answer))
            if len(key) > MAX_KEY_LEN:
                result['success'] = False
                result['errors'].append("Key '{0}' too long.".format(key))
            img = answer.get('img', '').strip()[:MAX_URL_LEN]
            label = answer.get('label', '').strip()[:MAX_ANSWER_LEN]
            if not (img or label):
                result['success'] = False
                result['errors'].append(
                    "Answer {0} has no text or img. One is needed.")
            answers.append((key, {'label': label, 'img': img}))

        if not len(answers) > 1:
            result['errors'].append(
                "You must include at least two answers.")
            result['success'] = False

        if not result['success']:
            return result

        self.answers = answers
        self.question = question
        self.feedback = feedback

        # Tally will not be updated until the next attempt to use it, per
        # scoping limitations.

        return result

    @XBlock.json_handler
    def vote(self, data, suffix=''):
        """
        An example handler, which increments the data.
        """
        result = {'success': False, 'errors': []}
        if self.get_choice() is not None:
            result['errors'].append('You have already voted in this poll.')
            return result
        try:
            choice = data['choice']
        except KeyError:
            result['errors'].append('Answer not included with request.')
            return result
        # Just to show data coming in...
        try:
            OrderedDict(self.answers)[choice]
        except KeyError:
            result['errors'].append('No key "{choice}" in answers table.'.format(choice=choice))
            return result

        self.clean_tally()
        self.choice = choice
        self.tally[choice] = self.tally.get(choice, 0) + 1
        # Let the LMS know the user has answered the poll.
        self.runtime.publish(self, 'progress', {})
        result['success'] = True

        return result

    @staticmethod
    def workbench_scenarios():
        """
        Canned scenarios for display in the workbench.
        """
        return [
            ("Default Poll",
             """
             <vertical_demo>
                 <poll />
             </vertical_demo>
             """),
            ("Customized Poll",
             """
             <vertical_demo>
                 <poll url_name="poll_functions" question="## How long have you been studying with us?"
                     feedback="### Thank you&#10;&#10;for being a valued student."
                     tally="{'long': 20, 'short': 29, 'not_saying': 15, 'longer' : 35}"
                     answers="[['long', 'A very long time'], ['short', 'Not very long'], ['not_saying', 'I shall not say'], ['longer', 'Longer than you']]"/>
            </vertical_demo>
             """),
        ]