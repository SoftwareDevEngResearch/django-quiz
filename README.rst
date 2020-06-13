===========
django-quiz
===========
This package is a Django application that provides users with the functionality to build quiz-format design tools.

Table of Contents
-----------------
* Requirements_
* `Getting Started`_

  *  `Without Django Installed`_
  *  `With Django Installed`_
* `Making a Quiz`_

  *  `CSV Formatting`_
  *  `Uploading a Quiz`_
* `Getting User Data`_
* License_

.. _Requirements:

Requirements
------------

* Python 3.7.4
* Django 3.03
* django-model-utils
* django-nested-admin
* xhtml2pdf
* jsonfield


For testing only:
* pytest 5.4.3
* pytest-django

.. `Getting Started`:

Getting Started
---------------

**NOTE: If you have not used Django before I recommend you read the "First Steps" section of the** `Django documentation <https://docs.djangoproject.com/en/3.0/>`_ **before using this package.**

.. `Without Django Installed`

Without Django Installed
************************

First you need to install Django

    python -m pip install Django


Now that Django is installed, you can start your Django project. Replace `project_name` with the name of your project.

    django-admin startproject project_name

Procceed to `With Django Installed`

.. `With Django Installed`

With Django Installed
*********************

Now navigate to the django-quiz folder and install the requirements. This command should ensure all the libraries you need for this project are installed.

    git clone https://github.com/aeronlroach/django-quiz.git


Then

    pip install -r requirements.txt
    

Then run

    python setup.py install


Add `"quizzes"` and `"nested_admin"` to your INSTALLED_APPS in your project's `settings.py`

    INSTALLED_APPS = (
        ...

        'quizzes',

        'nested_admin',

        ...

    )

Add the following to your project's `urls.py`

    from django.contrib import admin

    from django.urls import path, include

    from quizzes.views import quiz_upload

    urlpatterns = [

        path('quizzes/', include('quizzes.urls')),

        path('admin/', admin.site.urls),

        path('nested_admin/', include('nested_admin.urls')),

        path('upload-csv/', quiz_upload, name="quiz_upload"),

    ]

Now make your migrations and migrate your data with `python manage.py makemigrations` and `python manage.py migrate`

If you have not done so already, create a superuser account `python manage.py createsuperuser`and then check that the sever runs `python manage.py runserver`

Visit the local server at `127.0.0.1:8000/admin` to log-in and see the admin panel. After following the csv formatting instructions in `Making a Quiz`_, visit `127.0.0.1:8000/upload-csv` to upload your quiz build csv. If you receive an error trying to access `127.0.0.1:8000/upload-csv`, your admin session expired. You will need to login again.

.. _Making_a_Quiz:

Making a Quiz
-------------

It is recommended that you build a quiz using a csv file. While in-browser building is available, the relational linking must be completed manually. The csv method automates this process.

.. _CSV_Formatting:

CSV Formatting
**************
The first line of the csv is formatted as follows. Replace `QUIZ NAME` with the name of your quiz, the date field with the current date, and `DESCRIPTION OF QUIZ` with brief description of your quiz **NOTE: As this is a csv, you must surround your description with the quote character | Example: |This is my quiz, it is a test|** This line will establish the Quiz model. Replace `YYYY-MM-DD` with the date you are creating the quiz - follow the `YYYY-MM-DD` format.

    QUIZ NAME,YYYY-MM-DD,DESCRIPTION OF QUIZ

The rest of the csv follows this format.

    QUIZ NAME,CATEGORY 1 NAME,QUESTION 1 TEXT,ANSWER 1 TEXT,ANSWER WEIGHT,FEEDBACK TEXT FOR ANSWER 1

    QUIZ NAME,CATEGORY 1 NAME,QUESTION 1 TEXT,ANSWER 2 TEXT,ANSWER WEIGHT,FEEDBACK TEXT FOR ANSWER 2

    QUIZ NAME,CATEGORY 1 NAME ,QUESTION 1 TEXT,ANSWER 3 TEXT,ANSWER WEIGHT,FEEDBACK TEXT FOR ANSWER 3

These three lines represent a category that has question with has three answer choices. Example CSV files can be found in the "Example CSV Files" directory. **NOTE: As stated before, if you use commas for the text of questions/answers/feedback, you must surround the text with the quote character |** This folder also contains a stock template of the following format:

* Quiz
    *  Category 1
        *  Question 1
            *  Answer 1 with Custom Feedback if Selected
            *  Answer 2 with Custom Feedback if Selected
            *  Answer 3 with Custom Feedback if Selected
        *  Question 2
            *  Answer 1 with Custom Feedback if Selected
            *  Answer 2 with Custom Feedback if Selected
            *  Answer 3 with Custom Feedback if Selected
    *  Category 2
        *  Question 1
            *  Answer 1 with Custom Feedback if Selected
            *  Answer 2 with Custom Feedback if Selected
            *  Answer 3 with Custom Feedback if Selected
        *  Question 2
            *  Answer 1 with Custom Feedback if Selected
            *  Answer 2 with Custom Feedback if Selected
            *  Answer 3 with Custom Feedback if Selected


.. _Uploading_a_Quiz:

Uploading a Quiz
****************

After following the csv formatting instructions above start the server with:

    python manage.py runserver

Login at `127.0.0.1:8000/admin` and navigate to `127.0.0.1:8000/upload-csv`

From here, select `Browse...` and navigate to the directory where your quiz csv is stored, and select the csv.

Now press `Upload` and the page should refresh, if no error messages display - you have successfully built a quiz.

Navigating to `127.0.0.1:8000/quizzes` you should see the Title of the quiz on the quiz index. Your quiz is now stored in the database. Click `Info` to look at the Quiz detail view, or `Take Quiz` to start a quiz session


.. _Getting_User_Data:

Getting User Data
-----------------
To export user data from the database, I recommend using `DB Browser for SQlite <https://sqlitebrowser.org/>`_ while I develop an in-browser export feature.

.. _License:

License
-------
MIT License

Copyright (c) 2020 Software Development for Engineering Research

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
