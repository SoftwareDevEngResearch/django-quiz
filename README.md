# django-quiz
A django evaluation framework. Use to create a concept evaluation tool

# Current Functionality
To date, I have a limited build for the Django quiz framework. Currently, there are three main aspects to the quiz functionality.
* An administrative view where a superuser:
  * Can manually add each quiz, category, question, answer, answer weight, and feedback.
  * Needs to manually set the relations for each category, question, answer, and answer feedback.
  * Can set a quiz publish date. This will allow quizzes to be displayed only if the current date is on or after the “publish date.”
* A quiz index view:
  * Allows users to view a quiz and all the related categories, questions, and answers.
  * Contains a “take quiz” link that redirects the user to take the quiz.
    * The quiz pages through questions, meaning only one question is displayed at a time.
    * If no question is selected, the question page reloads with an error – asking the user to select an answer.
* After answering the final question, an “evaluation” page displays feedback for:
  * Categories with scores below a threshold value. Currently this is just the raw score, not a normalized score.
  * Answers in these categories with a weighting less than 1 (the highest score).
