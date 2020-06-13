import csv, io, datetime
from django.contrib.auth.decorators import permission_required
from django.views.decorators.cache import cache_page
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.views import generic
from django.utils import timezone
from .models import Quiz, Category, Question, Answer, Feedback, UserResponse
from .render import Render


# Built following alongside Django Software Foundation's Writing your first Django app Tutorial
# https://docs.djangoproject.com/en/3.0/intro/tutorial01/

class IndexView(generic.ListView):
    template_name = 'quizzes/index.html'
    context_object_name = 'latest_quiz_list'

    def get_queryset(self):
        """Return the last five published, active quizzes"""
        return Quiz.objects.filter(active_quiz=True).order_by('-pub_date')[:5]


class QuizDetailView(generic.DetailView):
    model = Quiz
    template_name = 'quizzes/quiz_detail.html'

    def get_queryset(self):
        """Return the active quizzes"""
        return Quiz.objects.filter(active_quiz=True).order_by('-pub_date')


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
    error_msg = 'This is csv file is not formatted correctly, please check the file and try again'

    if request.method == 'GET':
        return render(request, template, prompt)

    csv_file = request.FILES['file']

    # Check if the submitted file is .csv format
    if not csv_file.name.endswith('.csv'):
        messages.error(request, 'This is not a csv file')

    quiz_contents = csv_file.read().decode('UTF-8')
    io_string = io.StringIO(quiz_contents)

    # Create/Update Quiz using first row of csv, check for proper format
    csv_header = next(csv.reader(io_string, delimiter=',', quotechar="|"))
    try:
        # Added an extra layer of error catching, this will try to enter the time in the full datetime format
        # if not in datetime %Y-%m-%d %H:%M:%S.%f', then it will just try the date given
        try:
            quiz_obj, created = Quiz.objects.update_or_create(
                name=csv_header[0],
                pub_date=datetime.datetime.strptime(csv_header[1], '%Y-%m-%d %H:%M:%S.%f'),
                description=csv_header[2],
                active_quiz=True,
            )
        except ValueError:
            quiz_obj, created = Quiz.objects.update_or_create(
                name=csv_header[0],
                pub_date=csv_header[1],
                description=csv_header[2],
                active_quiz=True,
            )
    except IndexError:
        messages.error(request, error_msg)

    # Now create the rest of the Quiz elements
    for row in csv.reader(io_string, delimiter=',', quotechar="|"):
        try:
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
            answer = Answer.objects.filter(answer_text=row[3], parent_question=question).get()
            feedback_obj, created = Feedback.objects.update_or_create(
                parent_quiz=quiz,
                parent_category=category,
                parent_question=question,
                parent_answer=answer,
                feedback_type='',
                feedback_text=row[5]
            )
        except IndexError:
            messages.error(request, error_msg)

    context = {
        "success": 'The quiz was uploaded successfully',
        'header order': 'Order of the CSV header should be Quiz name, pub_date, description',
        'order': 'Order for rest of CSV should be Quiz name, '
                 'category_name, question_text, answer_text, answer_weight, feedback_text'}

    return render(request, template, context)


def create_user_response(quiz_id, *args):
    """
    Function to create a new response database entry,
    response_id is left default to be produced with the
    UserResponse class's generate_new_id function

    Returns the UserResponse object response_id
    """
    quiz = get_object_or_404(Quiz, pk=quiz_id)
    if args:
        response_obj, created = UserResponse.objects.update_or_create(
            parent_quiz=quiz,
            response_id=args[0]['user_id'],
            defaults=dict(response_data=args[0]['quiz_dictionary']),
        )
        return response_obj.response_id
    else:
        response_obj, created = UserResponse.objects.update_or_create(
            parent_quiz=quiz,
            response_id=0,
        )
        if response_obj.response_id is 0:
            response_obj, created = UserResponse.objects.update_or_create(
                parent_quiz=quiz,
                response_id=UserResponse.generate_new_id(response_obj, quiz_id),
            )

        return response_obj.response_id


def save_user_feedback(request, user_id):
    user = UserResponse.objects.filter(response_id=user_id).get()
    quiz = user.parent_quiz

    # Get session variables for rendering
    quiz_data = request.session[quiz.session_quiz_data()]
    feed_dict = request.session[quiz.session_feedback()]
    norm_scores_dict = request.session[quiz.session_norm_data()]

    # Updating session's UserResponse to
    create_user_response(quiz.id, {'user_id': user_id, 'quiz_dictionary': {'quiz_data': quiz_data,
                                                                           'quiz_norm_scores': norm_scores_dict,
                                                                           'feedback_data': feed_dict}})


def start_new_quiz(request, quiz_id, category_id):
    """
    Function to create a new quiz session variables when "Take Quiz" button is selected.
    """
    quiz = get_object_or_404(Quiz, pk=quiz_id)
    quiz_id = quiz.id
    categories = quiz.get_quiz_categories()
    category_id = quiz.category_set.first().id
    questions = quiz.get_quiz_questions()
    question_id = quiz.question_set.first().id
    question_list = [q.id for q in questions]

    # Set session variables for quiz
    request.session.flush()
    request.session[quiz.session_question_list()] = question_list

    # Quiz data dictionary formatted:
    # {category_name: {question_name : answer_selected} }
    data = {}
    for i in range(len(categories)):
        innerdict = {}
        category = categories[i]
        cat_questions = category.question_set.all()
        for j in range(len(cat_questions)):
            question_list_item = cat_questions[j]
            innerdict.update({question_list_item.question_text: None})
        data.update({category.category_name: innerdict})
    request.session[quiz.session_quiz_data()] = data

    category_score_data = {categories[i].category_name: None for i in range(len(categories))}
    request.session[quiz.session_cat_data()] = category_score_data
    request.session[quiz.session_norm_data()] = category_score_data

    # # Create new new user response
    user_id = create_user_response(quiz_id)
    request.session[quiz.session_response_id()] = user_id

    return HttpResponseRedirect(
        reverse('quizzes:take_quiz', args=(quiz.id, category_id, question_id)))


def take_quiz(request, quiz_id, category_id, question_id):
    """
    View Function that is responsible for rendering the question pages of the quiz
    """
    # Get vars
    quiz = get_object_or_404(Quiz, pk=quiz_id)
    question_id = Question.objects.get_subclass(id=question_id)
    return render(request, 'quizzes/take_quiz.html',
                  {'quiz': quiz.id, 'category': category_id, 'question': question_id})


def select_answer(request, quiz_id, category_id, question_id):
    """
    Function to submit an answer and continue paging through the quiz.
    If no more questions, redirects to feedback
    """

    # Get vars
    quiz = get_object_or_404(Quiz, pk=quiz_id)
    category = get_object_or_404(Category, pk=category_id)
    category_name = category.category_name
    question = get_object_or_404(Question, pk=question_id)
    question_text = question.question_text
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
        question_scores[str(category_name)][str(question_text)] = selected_answer.answer_text
        category_score = request.session[quiz.session_cat_data()]
        answer_score = selected_answer.answer_weight
        if category_score[str(category_name)] is None:
            category_score[str(category_name)] = answer_score
        elif category_score[str(category_name)] is not None:
            category_score[str(category_name)] = category_score[str(category_name)] + answer_score
        request.session[quiz.session_cat_data()] = category_score

        # Continue with quiz, or redirect to feedback when on last question
        if question_id == last_question:  # Finished Answering Questions for quiz, redirect to feedback
            normalize_scores(request, quiz_id)
            get_session_feedback(request, quiz_id)
            user_id = request.session[quiz.session_response_id()]
            save_user_feedback(request, user_id)
            return HttpResponseRedirect(reverse('quizzes:feedback', args=(user_id,)))
        else:
            return HttpResponseRedirect(reverse('quizzes:take_quiz', args=(quiz_id, category_id, question_id + 1)))


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

    Dictionary format: {category_name : normalized score}
    """
    quiz, quiz_data, category_score_dict, norm_score_dict, questions_list = get_session_data(request, quiz_id)
    categories = quiz.get_quiz_categories()

    # Creating a list of the max score for each section, needed to normalize to a score range of 0 - 10
    old_max_list = []
    for i in range(len(category_score_dict)):
        category = categories[i]
        old_max_list.append(len(quiz_data[str(category.category_name)]))

    # Normalizing the old scores and populating the session variable session_norm_data
    norm_score_list = [
        (10 / (old_max_list[i] - 0)) * (category_score_dict[str(categories[i].category_name)] - old_max_list[i]) + 10
        for i in range(len(category_score_dict))
    ]

    for i in range(len(category_score_dict)):
        category = categories[i]
        if norm_score_list[i] is not None:
            norm_score_dict[str(category.category_name)] = norm_score_list[i]
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
        category_name = category.category_name
        cat_questions = category.question_set.all()
        for j in range(len(cat_questions)):
            question = cat_questions[j]
            question = Question.objects.filter(id=question.id).get()
            question_text = question.question_text
            answer_text = quiz_data[str(category_name)][str(question_text)]
            if answer_text is not None:
                answer = Answer.objects.filter(answer_text=answer_text).get()
                if answer.answer_weight < 1:
                    feedback = answer.get_quiz_feedback().get()
                    innerdict.update({question_text: feedback.feedback_text})
                if answer.answer_weight == 1:
                    check_feedback = answer.get_quiz_feedback().get()
                    if check_feedback is "No Feedback":
                        feedback = None
                    else:
                        feedback = check_feedback
                    innerdict.update({question_text: feedback})
        feedback_set.update({category_name: innerdict})
    request.session[quiz.session_feedback()] = feedback_set
    return request.session[quiz.session_feedback()]


@cache_page(60 * 15)
def feedback(request, user_id):
    """
    This is the feedback page that users will see once they are done with a quiz.
    This page is cached and uses the UserResponse Model to show a limited amount of feedback
    """
    request.session.set_expiry(1)
    user = UserResponse.objects.filter(response_id=user_id).get()
    quiz = user.parent_quiz

    # Get session variables for rendering
    quiz_data = user.response_data['quiz_data']
    norm_scores_dict = user.response_data['quiz_norm_scores']
    feed_dict = user.response_data['feedback_data']
    number_of_sections = 2
    sorted_scores_limited = {k: v
                             for k, v in sorted(norm_scores_dict.items(), key=lambda item: item[1])[:number_of_sections]
                             }

    return render(request, 'quizzes/feedback.html', {
        'quiz': quiz,
        'feed_dict': feed_dict,
        'norm_scores': norm_scores_dict,
        'sorted_scores_limit': sorted_scores_limited,
        'user_id': user_id
    })


@cache_page(60 * 60)
def get_feedback_pdf(request, user_id):
    """
    This is a feedback page that is rendered as a pdf. Users will be able to access this from the feedback page.
    This page is cached and uses the response_data object of the UserResponse Model.
    """
    today = timezone.now()
    user = UserResponse.objects.filter(response_id=user_id).get()
    quiz = user.parent_quiz

    # Get session variables for rendering
    quiz_data = user.response_data['quiz_data']
    norm_scores_dict = user.response_data['quiz_norm_scores']
    feed_dict = user.response_data['feedback_data']
    context = {
        'user_id': user_id,
        'today': today,
        'quiz': quiz,
        'quiz_data': quiz_data,
        'feed_dict': feed_dict,
        'norm_scores': norm_scores_dict,
    }
    return Render.render('quizzes/get_feedback_pdf.html', context)
