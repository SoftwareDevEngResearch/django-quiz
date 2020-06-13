from django.test import TestCase

import datetime

from django.test import TestCase
from django.utils import timezone
from django.urls import reverse
from django.test import Client

from .models import Quiz, Category, Question, Answer, Feedback, UserResponse
from .views import create_user_response, save_user_feedback, feedback, get_feedback_pdf


# Built following alongside Django Software Foundation's Writing your first Django app Tutorial
# https://docs.djangoproject.com/en/3.0/intro/tutorial01/
# Making a change to trigger travis

def create_quiz(quiz_name, days, active_level):
    """
    Create a quizzes with the given `quiz_name`, created the
    given number of `days` offset to now (negative for quizzes published
    in the past, positive for quizzes that have yet to be published).
    "active_level" is a boolean, with False meaning Inactive and True meaning active.
    """
    time = timezone.now() + datetime.timedelta(days=days)
    quiz = Quiz.objects.create(name=quiz_name, pub_date=time, active_quiz=active_level)
    category = Category.objects.create(parent_quiz=quiz, category_name="test catergory")
    question = Question.objects.create(parent_quiz=quiz, parent_category=category,
                                       question_text="How's this test question?")
    answer_1h = Answer.objects.create(parent_quiz=quiz, parent_category=category, parent_question=question,
                                      answer_text="Great!", answer_weight=1)
    answer_1l = Answer.objects.create(parent_quiz=quiz, parent_category=category, parent_question=question,
                                      answer_text="BOO!", answer_weight=0)
    feedback_1h = Feedback.objects.create(parent_quiz=quiz, parent_category=category, parent_question=question,
                                          parent_answer=answer_1h, feedback_text="No feedback")
    feedback_1l = Feedback.objects.create(parent_quiz=quiz, parent_category=category, parent_question=question,
                                          parent_answer=answer_1l, feedback_text="Give up, it be hopeless")
    return quiz, category, question, answer_1h, answer_1l, feedback_1h, feedback_1l


class QuizModelTests(TestCase):

    def test_published_recently_future(self):
        """
        was_published_recently() returns False for quizzes whose pub_date
        is in the future.
        """
        time = timezone.now() + datetime.timedelta(days=30)
        future_quiz = Quiz(pub_date=time)
        self.assertIs(future_quiz.was_published_recently(), False)

    def test_published_recently_old(self):
        """
        was_published_recently() returns False for quizzes whose pub_date
        is older than 1 day.
        """
        time = timezone.now() - datetime.timedelta(days=1, seconds=1)
        old_quiz = Quiz(pub_date=time)
        self.assertIs(old_quiz.was_published_recently(), False)

    def test_published_recently_recent(self):
        """
        was_published_recently() returns True for quizzes whose pub_date
        is within the last day.
        """
        time = timezone.now() - datetime.timedelta(hours=23, minutes=59, seconds=59)
        recent_quiz = Quiz(pub_date=time)
        self.assertIs(recent_quiz.was_published_recently(), True)

    def test_awake(self):
        """
         check_active() returns True for active quizzes
        """
        activated_quiz = Quiz(active_quiz=True)
        self.assertIs(activated_quiz.check_active(), True)

    def test_sleep(self):
        """
        check_active() returns False for inactive quizzes
        """
        inactive_quiz = Quiz(active_quiz=True)
        self.assertIs(inactive_quiz.check_active(), True)


class QuizIndexViewTests(TestCase):
    def test_no_quizzes(self):
        """
        If no quizzes exist, an appropriate message is displayed.
        """
        response = self.client.get(reverse('quizzes:index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No quizzes are available.")
        self.assertQuerysetEqual(response.context['latest_quiz_list'], [])

    def test_awake_quiz(self):
        """
        Active Quizzes are displayed on the index page.
        """
        create_quiz(quiz_name="Awake quizzes.", days=-30, active_level=True)
        response = self.client.get(reverse('quizzes:index'))
        self.assertQuerysetEqual(
            response.context['latest_quiz_list'],
            ['<Quiz: Awake quizzes.>']
        )

    def test_sleep_quiz(self):
        """
        Inactive quizzes aren't displayed on
        the index page.
        """
        create_quiz(quiz_name="Sleep quizzes.", days=-30, active_level=False)
        response = self.client.get(reverse('quizzes:index'))
        self.assertContains(response, "No quizzes are available.")
        self.assertQuerysetEqual(response.context['latest_quiz_list'], [])

    def test_awake_and_sleep(self):
        """
        Even if both active and inactive quizzes exist, only active quizzes
        are displayed.
        """
        create_quiz(quiz_name="Awake quizzes.", days=-30, active_level=True)
        create_quiz(quiz_name="Sleep quizzes.", days=-30, active_level=False)
        response = self.client.get(reverse('quizzes:index'))
        self.assertQuerysetEqual(
            response.context['latest_quiz_list'],
            ['<Quiz: Awake quizzes.>']
        )

    def test_two_awake(self):
        """
        The quizzes index page may display multiple active quizzes.
        """
        create_quiz(quiz_name="Awake quizzes 1.", days=-30, active_level=True)
        create_quiz(quiz_name="Awake quizzes 2.", days=-5, active_level=True)
        response = self.client.get(reverse('quizzes:index'))
        self.assertQuerysetEqual(
            response.context['latest_quiz_list'],
            ['<Quiz: Awake quizzes 2.>', '<Quiz: Awake quizzes 1.>']
        )

    def no_future_quiz(self):
        """
        Quizzes with pub-dates in future do not show, even if active
        """
        create_quiz(quiz_name="Awake quizzes 1.", days=3, active_level=True)
        response = self.client.get(reverse('quizzes:index'))
        self.assertQuerysetEqual(
            response.context['latest_quiz_list'],[]
        )


class QuizDetailViewTests(TestCase):
    def test_sleep_quiz(self):
        """
        The detail view of inactive quizzes returns a 404 not found.
        """
        sleep_quiz = create_quiz(quiz_name='Sleep quizzes.', days=-5, active_level=False)
        url = reverse('quizzes:quiz_detail', args=(sleep_quiz[0].id,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_awake_quiz(self):
        """
        The detail view of active quizzes returns the quiz nanme.
        """
        past_quiz = create_quiz(quiz_name='Awake quizzes.', days=-5, active_level=True)
        url = reverse('quizzes:quiz_detail', args=(past_quiz[0].id,))
        response = self.client.get(url)
        self.assertContains(response, past_quiz[0].name)


class TakingQuizVTests(TestCase):
    def test_new_quiz(self):
        """
        The start_new_quiz function should redirect to take_quiz when run.
        """
        quiz = create_quiz(quiz_name="test quiz", days=-5, active_level=True)
        url = reverse('quizzes:start_new_quiz', args=(quiz[0].id, quiz[1].id))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

    def test_take_quiz(self):
        """
        take_quiz should have the data for name of a quiz
        """
        quiz = create_quiz(quiz_name="test quiz", days=-5, active_level=True)
        url = reverse('quizzes:take_quiz', args=(quiz[0].id, quiz[1].id, quiz[2].id))
        response = self.client.get(url)
        self.assertContains(response, quiz[0].name)

    def test_select_answer(self):
        """
        A post request on take_quiz should include the answer id, and should return a 200 code
        """
        c = Client()
        quiz = create_quiz(quiz_name="test quiz", days=-5, active_level=True)
        url = reverse('quizzes:take_quiz', args=(quiz[0].id, quiz[1].id, quiz[2].id))
        post = c.post(url, {'question': quiz[2], 'answer': quiz[3]})
        self.assertContains(post, quiz[3].id)
        self.assertEqual(post.status_code, 200)


class CreatingUserResponses(TestCase):
    def test_create_new_response(self):
        """
        A newly created user response should have a parent_quiz that matches quiz the user is taking
        """
        quiz = create_quiz(quiz_name="test quiz", days=-5, active_level=True)[0]
        responseid = create_user_response(quiz.id)
        userresponse = UserResponse.objects.filter(response_id=responseid)[0]
        self.assertEqual(userresponse.parent_quiz, quiz)