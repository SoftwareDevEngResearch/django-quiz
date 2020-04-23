from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.views import generic
from django.utils import timezone
from .models import Quiz, Category, Question, Answer, Feedback
from django.contrib.sessions.backends.db import SessionStore


# Built following alongside Django Software Foundation's Writing your first Django app Tutorial
# https://docs.djangoproject.com/en/3.0/intro/tutorial01/

class IndexView(generic.ListView):
    template_name = 'quizzes/index.html'
    context_object_name = 'latest_quiz_list'

    def get_queryset(self):
        """Return the last five published quizzes"""
        return Quiz.objects.filter(pub_date__lte=timezone.now()).order_by('-pub_date')[:5]


class QuizDetailView(generic.DetailView):
    model = Quiz
    template_name = 'quizzes/quiz_detail.html'

    def get_queryset(self):
        """Return the last five published quizzes"""
        return Quiz.objects.filter(pub_date__lte=timezone.now())


class CategoryDetailView(generic.DetailView):
    model = Category
    template_name = 'quizzes/category_detail.html'


class QuestionDetailView(generic.DetailView):
    model = Question
    template_name = 'quizzes/question_detail.html'


def feedback(request, quiz_id):
    quiz = get_object_or_404(Quiz, pk=quiz_id)
    return render(request, 'quizzes/feedback.html', {
        'quiz': quiz,
        'feed_dict': request.session[quiz.session_feedback()],
        'norm_scores': request.session[quiz.session_norm_data()],
        })


def new_quiz(request, quiz_id, category_id):
    """
    Function to create a new session when "Take Quiz" is selected.
    """
    quiz = get_object_or_404(Quiz, pk=quiz_id)
    quiz_id = quiz.id
    categories = quiz.get_quiz_categories()
    category_id = quiz.category_set.first().id
    questions = quiz.get_quiz_questions()
    question_id = quiz.question_set.first().id
    question_list = [q.id for q in questions]

    # Reset Quiz session
    request.session.flush()
    request.session.set_expiry(120)

    # Reset the category score values to zero
    Category.objects.values_list('score').update(score=0)
    # Reset the answer values to false
    Answer.objects.values_list('answer_selected').update(answer_selected=False)

    # Set session variables for quiz
    request.session[quiz.session_question_list()] = question_list

    # Quiz data dictionary formatted:
    # {category_id: {question_id : answer_selected} }
    data = {}
    for i in range(len(categories)):
        innerdict = {}
        category = categories[i]
        cat_questions = category.question_set.all()
        for j in range(len(cat_questions)):
            question_list_item = cat_questions[j]
            innerdict.update({question_list_item.id: None})
        data.update({categories[i].id: innerdict})
    request.session[quiz.session_quiz_data()] = data

    category_data = {categories[i].id: None for i in range(len(categories))}
    request.session[quiz.session_cat_data()] = category_data
    request.session[quiz.session_norm_data()] = category_data

    return HttpResponseRedirect(
        reverse('quizzes:take_quiz', args=(quiz.id, category_id, question_id)))  # take_quiz(request, quiz, question)


def take_quiz(request, quiz_id, category_id, question_id):
    """
    View Function that is responsible for rendering the question pages of the quiz
    """
    # Get vars
    quiz = get_object_or_404(Quiz, pk=quiz_id)
    question_id = Question.objects.get_subclass(id=question_id)
    return render(request, 'quizzes/take_quiz.html',
                  {'quiz': quiz.id, 'category': category_id, 'question': question_id})


def get_session_data(request, quiz_id):
    """
    Helper function that takes the request and quiz_id as arguments and returns
    useful variables
    """
    quiz = get_object_or_404(Quiz, pk=quiz_id)
    quiz_data = request.session[quiz.session_quiz_data()]
    category_score_dict = request.session[quiz.session_cat_data()]
    norm_score_dict = request.session[quiz.session_norm_data()]
    questions_list = request.session[quiz.session_question_list()]
    return quiz, quiz_data, category_score_dict, norm_score_dict, questions_list


def normalize_scores(request, quiz_id):
    """
    This is a function to normalize the category scores to a scale of 0-10. I have assumed that the max weight
    for each question is 1, and the min is 0. I will need to update this to adapt to the varying max and min
    weights from each question, as well as adapting to admin defined score ranges.

    Dictionary format: {category_id : normalized score}
    """
    quiz, quiz_data, category_score_dict, norm_score_dict, questions_list = get_session_data(request, quiz_id)
    categories = quiz.get_quiz_categories()

    # Creating a list of the max score for each section, needed to normalize to a score range of 0 - 10
    old_max_list = []
    for i in range(len(category_score_dict)):
        category = categories[i]
        old_max_list.append(len(quiz_data[str(category.id)]))

    # Normalizing the old scores and populating the session variable session_norm_data
    norm_score_list = [
        (10 / (old_max_list[i] - 0)) * (category_score_dict[str(categories[i].id)] - old_max_list[i]) + 10
        for i in range(len(category_score_dict))
    ]

    for i in range(len(category_score_dict)):
        category = categories[i]
        if norm_score_list[i] is not None:
            norm_score_dict[str(category.id)] = norm_score_list[i]
    request.session[quiz.session_norm_data()] = norm_score_dict
    return request.session[quiz.session_norm_data()]


def results(request, quiz_id):
    """
    Function to create a dictionary of feedback for the session
    Returns a dictionary formatted:
    {category_name: {question_text : feedback_text} }
    """
    quiz, quiz_data, category_score_dict, norm_score_dict, questions_list = get_session_data(request, quiz_id)
    categories = quiz.get_quiz_categories()

    # Creating the feedback dictionary to populate the session variable session_feedback
    feedback_set = {}
    for i in range(len(categories)):
        innerdict = {}
        category = categories[i]
        cat_questions = category.question_set.all()
        for j in range(len(cat_questions)):
            question = cat_questions[j]
            question = Question.objects.filter(id=question.id).get()
            answer_text = quiz_data[str(category.id)][str(question.id)]
            if answer_text is not None:
                answer = Answer.objects.filter(answer_text=answer_text).get()
                if answer.answer_weight < 1:
                    feedback = answer.get_quiz_feedback().get()
                    innerdict.update({question.question_text: feedback.feedback_text})
        feedback_set.update({category.category_name: innerdict})
    request.session[quiz.session_feedback()] = feedback_set
    return request.session[quiz.session_feedback()]


def select_answer(request, quiz_id, category_id, question_id):
    """
    Function to submit an answer and continue paging through the quiz. If no more questions, redirects to feedback
    """

    # Get vars
    quiz = get_object_or_404(Quiz, pk=quiz_id)
    category = get_object_or_404(Category, pk=category_id)
    question = get_object_or_404(Question, pk=question_id)
    # last_question = len(quiz.question_set.all())
    last_question = request.session[quiz.session_question_list()][-1]

    try:  # Check if an answer is selected
        selected_answer = question.answer_set.get(pk=request.POST['answer'])
    except (KeyError, Answer.DoesNotExist):
        # Redisplay the question if answer is not selected
        return render(request, 'quizzes/take_quiz.html', {
            'quiz': quiz,
            'question': question,
            'error_message': "You didn't select an answer.",
        })
    else:
        # Update parameters based on selection
        # selected_answer.answer_selected = True
        question_scores = request.session[quiz.session_quiz_data()]
        question_scores[str(category_id)][str(question_id)] = selected_answer.answer_text
        category_score = request.session[quiz.session_cat_data()]
        answer_score = selected_answer.answer_weight
        if category_score[str(category_id)] is None:
            category_score[str(category_id)] = answer_score
        elif category_score[str(category_id)] is not None:
            category_score[str(category.id)] = category_score[str(category.id)] + answer_score
        request.session[quiz.session_cat_data()] = category_score
        # category_score = category.score
        # answer_score = selected_answer.answer_weight
        # Category.objects.filter(id=category_id).update(score=category_score + answer_score)
        # selected_answer.save()

        # Continue with quiz, or redirect to feedback when on last question
        if question_id == last_question:  # Finished Answering Questions for quiz, redirect to feedback
            normalize_scores(request, quiz_id)
            results(request, quiz_id)
            return HttpResponseRedirect(reverse('quizzes:feedback', args=(quiz_id,)))
        else:
            return HttpResponseRedirect(reverse('quizzes:take_quiz', args=(quiz_id, category_id, question_id + 1)))
