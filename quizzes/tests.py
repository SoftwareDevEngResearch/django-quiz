from django.test import TestCase

import datetime

from django.test import TestCase
from django.utils import timezone
from django.urls import reverse

from .models import Quiz

# Built following alongside Django Software Foundation's Writing your first Django app Tutorial
# https://docs.djangoproject.com/en/3.0/intro/tutorial01/


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

    def test_active(self):
        """
         check_active() returns True for active quizzes
        """
        activated_quiz = Quiz(active_quiz=True)
        self.assertIs(activated_quiz.check_active(),True)

    def test_inactive(self):
        """
        check_active() returns False for inactive quizzes
        """
        inactive_quiz = Quiz(active_quiz=True)
        self.assertIs(inactive_quiz.check_active(),True)


def create_quiz(quiz_name, days):
    """
    Create a quizzes with the given `quiz_name` and published the
    given number of `days` offset to now (negative for quizzes published
    in the past, positive for quizzes that have yet to be published).
    """
    time = timezone.now() + datetime.timedelta(days=days)
    return Quiz.objects.create(quiz_name=quiz_name, pub_date=time)


class QuizIndexViewTests(TestCase):
    def test_no_quizzes(self):
        """
        If no quizzes exist, an appropriate message is displayed.
        """
        response = self.client.get(reverse('quizzes:index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No quizzes are available.")
        self.assertQuerysetEqual(response.context['latest_quiz_list'], [])

    def test_past_quiz(self):
        """
        Quizzes with a pub_date in the past are displayed on the
        index page.
        """
        create_quiz(quiz_name="Past quizzes.", days=-30)
        response = self.client.get(reverse('quizzes:index'))
        self.assertQuerysetEqual(
            response.context['latest_quiz_list'],
            ['<Quiz: Past quizzes.>']
        )

    def test_future_quiz(self):
        """
        Quizzes with a pub_date in the future aren't displayed on
        the index page.
        """
        create_quiz(quiz_name="Future quizzes.", days=30)
        response = self.client.get(reverse('quizzes:index'))
        self.assertContains(response, "No quizzes are available.")
        self.assertQuerysetEqual(response.context['latest_quiz_list'], [])

    def test_future_quiz_and_past_quiz(self):
        """
        Even if both past and future quizzes exist, only past quizzes
        are displayed.
        """
        create_quiz(quiz_name="Past quizzes.", days=-30)
        create_quiz(quiz_name="Future quizzes.", days=30)
        response = self.client.get(reverse('quizzes:index'))
        self.assertQuerysetEqual(
            response.context['latest_quiz_list'],
            ['<Quiz: Past quizzes.>']
        )

    def test_two_past_questions(self):
        """
        The questions index page may display multiple questions.
        """
        create_quiz(quiz_name="Past quizzes.", days=-30)
        create_quiz(quiz_name="Past quizzes.", days=-5)
        response = self.client.get(reverse('quizzes:index'))
        self.assertQuerysetEqual(
            response.context['latest_quiz_list'],
            ['<Quiz: Past quizzes 2.>', '<Quiz: Past quizzes 1.>']
        )


class QuizDetailViewTests(TestCase):
    def test_future_quiz(self):
        """
        The detail view of quizzes with a pub_date in the future
        returns a 404 not found.
        """
        future_quiz = create_quiz(quiz_name='Future quizzes.', days=5)
        url = reverse('quizzes:quiz_detail', args=(future_quiz.id,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_past_quiz(self):
        """
        The detail view of quizzes with a pub_date in the past
        displays the quizzes's name.
        """
        past_quiz = create_quiz(quiz_name='Past quizzes.', days=-5)
        url = reverse('polls:detail', args=(past_quiz.id,))
        response = self.client.get(url)
        self.assertContains(response, past_quiz.quiz_name)
