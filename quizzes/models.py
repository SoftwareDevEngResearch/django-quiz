import datetime
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


# Structure Idea comes from:
# https://codereview.stackexchange.com/questions/114962/model-classes-for-a-quiz-app-in-django
# Rest was built following alongside Django Software Foundation's Writing your first Django app Tutorial
# https://docs.djangoproject.com/en/3.0/intro/tutorial01/

class Quiz(models.Model):
    """Stores the name of the quiz and all data related to the quiz"""

    # Question content
    name = models.CharField(_("Quiz Name"), max_length=200, blank=True, null=True)
    pub_date = models.DateTimeField('date published')
    description = models.CharField(_("Quiz Description"), max_length=200, blank=True, null=True)

    def __str__(self):
        return self.name

    def was_published_recently(self):
        now = timezone.now()
        return now - datetime.timedelta(days=1) <= self.pub_date <= now

    def get_queryset(self):
        """Return the last five published quizzes"""
        return Quiz.objects.filter(pub_date__lte=timezone.now()).order_by('-pub_date')[:5]

    class Meta:
        verbose_name_plural = 'Quizzes'
        db_table = "quiz"


class Category(models.Model):
    """Stores the name of the category and the related quiz"""
    # Parent object
    parent_quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, blank=True, null=True)

    # Category content
    category_name = models.CharField(_("Category Name"), max_length=200, blank=True, null=True)
    order = models.IntegerField(blank=True, null=True)
    description = models.CharField(_("Category Description"), max_length=2000, blank=True, null=True)
    score = models.FloatField(default=0)

    def __str__(self):
        return self.category_name

    class Meta:
        db_table = "category"
        verbose_name_plural = 'Categories'


class Question(models.Model):
    """Each question is linked to a quiz and a category"""
    # Parent Object
    parent_quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, blank=True, null=True)
    parent_category = models.ForeignKey(Category, on_delete=models.CASCADE, blank=True, null=True)

    # Question Content
    question_text = models.CharField(_("Question"), max_length=600, blank=True, null=True)

    def __str__(self):
        return self.question_text

    class Meta:
        db_table = "question"


class Answer(models.Model):
    """Each answer is linked to a quiz, category, and question"""
    # Parent object
    parent_quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, blank=True, null=True)
    parent_category = models.ForeignKey(Category, on_delete=models.CASCADE, blank=True, null=True)
    parent_question = models.ForeignKey(Question, on_delete=models.CASCADE, blank=True, null=True)

    # Answer content
    answer_text = models.CharField(_("Answer"), max_length=600, blank=True, null=True)
    answer_selected = models.BooleanField(default=False)
    answer_weight = models.FloatField(default=1.0)

    def __str__(self):
        return self.answer_text

    class Meta:
        db_table = "answer"


class Feedback(models.Model):
    """
    Feedback is provided to each quiz participant upon completion.
    This feedback is tied to the selected answer for each question.
    """
    # Parent object
    parent_quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, blank=True, null=True)
    parent_category = models.ForeignKey(Category, on_delete=models.CASCADE, blank=True, null=True)
    parent_question = models.ForeignKey(Question, on_delete=models.CASCADE, blank=True, null=True)
    parent_answer = models.ForeignKey(Answer, on_delete=models.CASCADE, blank=True, null=True)

    # Feedback content
    feedback_type = models.CharField(_("Feedback Type"), max_length=200, blank=True, null=True)
    feedback_text = models.CharField(_("Feedback"), max_length=600, blank=True, null=True)

    def __str__(self):
        return self.feedback_text

    class Meta:
        db_table = "feedback"
        verbose_name_plural = 'Feedback'