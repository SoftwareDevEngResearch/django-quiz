from django.urls import path

from . import views

app_name = 'quizzes'

urlpatterns = [
    # ex: /quizzes/
    # Shows all quizzes
    path('', views.IndexView.as_view(), name='index'),

    # ex: /quizzes/1/
    # Shows all categories of quiz
    # The 'name' value as called by the {% url %} template tag
    path('<int:pk>/', views.QuizDetailView.as_view(), name='quiz_detail'),

    # ex: /quizzes/1/1/
    # Shows all questions in a category
    # The 'name' value as called by the {% url %} template tag
    path('<int:pk>/category/<int:pk1>/', views.CategoryDetailView.as_view(), name='category_detail'),

    # # ex: /quizzes/1/category/1/question/1
    # # Shows all the answer choices to a question
    path('<int:pk>/category/<int:pk1>/question/<int:pk3>/', views.QuestionDetailView.as_view(), name='question_detail'),

    # ex: /quizzes/1/1/question/1
    # Pages through the quiz questions
    path('<int:quiz_id>/<int:category_id>/<int:question_id>/', views.take_quiz, name='take_quiz'),

    # ex: /quizzes/1/1/question/1/select_answer
    path('<int:quiz_id>/<int:category_id>/<int:question_id>/select_answer/', views.select_answer, name='select_answer'),

    path('<int:quiz_id>/<int:category_id>/startquiz/', views.new_quiz, name='new_quiz'),

    # ex: /quizzes/1/feedback/user_id
    # Shows the user the feedback for their quiz
    path('<int:quiz_id>/feedback/', views.feedback, name='feedback'),
]