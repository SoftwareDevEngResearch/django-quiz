from django.urls import path
from . import views

app_name = 'quizzes'

urlpatterns = [
    # ex: /quizzes/
    # Shows all quizzes
    path('', views.IndexView.as_view(), name='index'),

    # ex: /quizzes/1/
    # Shows all categories and questions of quiz
    # The 'name' value as called by the {% url %} template tag
    path('<int:pk>/', views.QuizDetailView.as_view(), name='quiz_detail'),

    # ex: /quizzes/1/1/question/1
    # Pages through the quiz questions
    path('<int:quiz_id>/<int:category_id>/<int:question_id>/', views.take_quiz, name='take_quiz'),

    # ex: /quizzes/1/1/question/1/select_answer
    path('<int:quiz_id>/<int:category_id>/<int:question_id>/select_answer/', views.select_answer, name='select_answer'),

    # nothing is rendered on this page, just a quick jump between the index and take_quiz
    path('<int:quiz_id>/<int:category_id>/startquiz/', views.start_new_quiz, name='start_new_quiz'),

    # ex: /quizzes/feedback/user_id
    # Shows the user the feedback for their quiz
    path('feedback/<int:user_id>/', views.feedback, name='feedback'),

    # ex: /quizzes/feedback/user_id/pdf
    # Shows the user the feedback for their quiz
    path('feedback/<int:user_id>/pdf/', views.get_feedback_pdf, name='get_feedback_pdf'),
]