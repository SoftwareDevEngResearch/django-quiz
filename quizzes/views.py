import csv, io, datetime
from django.contrib.auth.decorators import permission_required
from django.contrib import messages
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
        """Return the last five published, active quizzes"""
        return Quiz.objects.filter(active_quiz__lte=True).order_by('-pub_date')[:5]


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
    feed_dict = request.session[quiz.session_feedback()]
    norm_scores_dict = request.session[quiz.session_norm_data()]
    number_of_sections = 2
    sorted_scores_limited = {k: v for k, v in sorted(norm_scores_dict.items(), key=lambda item: item[1])[:number_of_sections]}
    return render(request, 'quizzes/feedback.html', {
        'quiz': quiz,
        'feed_dict': feed_dict,
        'norm_scores': norm_scores_dict,
        'sorted_scores_limit': sorted_scores_limited,
        })


@permission_required('admin.can_add_log_entry')
def quiz_upload(request):
    """
    This is a function that lets the superuser upload a CSV to create a new quiz.
    """
    template = "quizzes/quiz_upload.html"
    prompt = {
        'header order': 'Order of the CSV header should be Quiz name, pub_date, description',
        'order': 'Order for rest of CSV should be Quiz name, '
                 'category_name, question_text, answer_text, answer_weight, feedback_text'
    }
    if request.method == 'GET':
        return render(request, template, prompt)

    csv_file = request.FILES['file']

    if not csv_file.name.endswith('.csv'):
        messages.error(request,'This is not a csv file')

    quiz_contents = csv_file.read().decode('UTF-8')
    io_string = io.StringIO(quiz_contents)
    for row in csv.reader(io_string, delimiter= ',',quotechar="|"):
        if len(row) <= 3:
            try:
                quiz_obj, created = Quiz.objects.update_or_create(
                    name=row[0],
                    # Just using this because I couldn't get my csv datetime formatted correctly,
                    # this will change when active/inactive is implemented
                    pub_date=datetime.datetime.strptime(row[1], '%Y-%m-%d %H:%M:%S.%f'),
                    description=row[2]
                )
            except IndexError:
                quiz, created = Quiz.objects.update_or_create(
                    name=row[0],
                    # Same as above
                    pub_date=datetime.datetime.strptime(row[1], '%Y-%m-%d %H:%M:%S.%f'),
                    description=''
                )
        else:
            quiz = Quiz.objects.filter(name=row[0]).get()
            category_obj, created = Category.objects.update_or_create(
                parent_quiz=quiz,
                category_name=row[1],
                order=0,
                description='',
                score=0
            )
            category = Category.objects.filter(category_name=row[1]).get()
            question_obj, created = Question.objects.update_or_create(
                parent_quiz=quiz,
                parent_category=category,
                question_text=row[2]
            )
            question = Question.objects.filter(question_text=row[2]).get()
            answer_obj, created = Answer.objects.update_or_create(
                parent_quiz=quiz,
                parent_category=category,
                parent_question=question,
                answer_text=row[3],
                answer_selected=False,
                answer_weight=row[4]
            )
            answer = Answer.objects.filter(answer_text=row[3]).get()
            feedback_obj, created = Feedback.objects.update_or_create(
                parent_quiz=quiz,
                parent_category=category,
                parent_question=question,
                parent_answer=answer,
                feedback_type='',
                feedback_text=row[5]
            )
    context = {
        "success": 'The quiz was uploaded successfully',
        'headerorder': 'Order of the CSV header should be Quiz name, pub_date, description',
        'order': 'Order for rest of CSV should be Quiz name, '
                 'category_name, question_text, answer_text, answer_weight, feedback_text'}
    return render(request, template, context)


def new_quiz(request, quiz_id, category_id):
    """
    Function to create a new quiz session when "Take Quiz" button is selected.
    """
    quiz = get_object_or_404(Quiz, pk=quiz_id)
    quiz_id = quiz.id
    categories = quiz.get_quiz_categories()
    category_id = quiz.category_set.first().id
    questions = quiz.get_quiz_questions()
    question_id = quiz.question_set.first().id
    question_list = [q.id for q in questions]

    # Delete expired sessions and set a new session
    request.session.flush()
    request.session.set_expiry(120)

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


def get_session_feedback(request, quiz_id):
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
        # Update session variables based on selection
        question_scores = request.session[quiz.session_quiz_data()]
        question_scores[str(category_id)][str(question_id)] = selected_answer.answer_text
        category_score = request.session[quiz.session_cat_data()]
        answer_score = selected_answer.answer_weight
        if category_score[str(category_id)] is None:
            category_score[str(category_id)] = answer_score
        elif category_score[str(category_id)] is not None:
            category_score[str(category.id)] = category_score[str(category.id)] + answer_score
        request.session[quiz.session_cat_data()] = category_score

        # Continue with quiz, or redirect to feedback when on last question
        if question_id == last_question:  # Finished Answering Questions for quiz, redirect to feedback
            normalize_scores(request, quiz_id)
            get_session_feedback(request, quiz_id)
            return HttpResponseRedirect(reverse('quizzes:feedback', args=(quiz_id,)))
        else:
            return HttpResponseRedirect(reverse('quizzes:take_quiz', args=(quiz_id, category_id, question_id + 1)))
