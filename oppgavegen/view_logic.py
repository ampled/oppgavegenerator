"""

Defines reusable functions often called from views.py

"""
from oppgavegen.models import Template, Topic, UserLevelProgress, Level, Tag
#from oppgavegen import generation
from oppgavegen.generation import replace_variables_from_array, parse_answer, parse_solution, replace_words, \
    calculate_array, template_validation
from datetime import datetime
from django.contrib.auth.models import User
from oppgavegen.answer_checker import check_answer
from oppgavegen.decorators import Debugger
from oppgavegen.generation_folder.fill_in import get_values_from_position
from oppgavegen.generation_folder.utility import after_equal_sign


def make_edit_context_dict(template_id):
    """Returns context dict for use on the edit page"""
    q = Template.objects.get(pk=template_id)
    calculation_references = q.calculation_ref
    question_text = q.question_text_latex
    solution = q.solution_latex
    answer = q.answer_latex
    choices = q.choices_latex
    conditions = q.conditions_latex
    fill_in = q.fill_in_latex
    topic = q.topic
    random_domain = q.random_domain
    unchanged_ref = q.unchanged_ref
    dictionary = q.dictionary
    used_variables = q.used_variables
    topics = ""
    for e in Topic.objects.all():
        topics += '§' + str(e.pk) + '§'
        topics += e.topic
    topics = topics[1:]
    context_dict = {'template_id': template_id, 'answer': answer, 'solution': solution,
                    'question_text': question_text, 'calculation_references': calculation_references,
                    'choices': choices, 'conditions': conditions, 'fill_in': fill_in,
                    'topic': topic, 'random_domain': random_domain, 'unchanged_ref': unchanged_ref,
                    'topics': topics, 'dictionary': dictionary, 'used_variables': used_variables}
    return context_dict


def make_answer_context_dict(form_values):
    """Returns context dict for use on the answer page"""
    user_answer = form_values['user_answer']
    template_type = form_values['template_type']
    template_specific = form_values['template_specific']
    q = Template.objects.get(pk=form_values['primary_key'])
    variable_dictionary = form_values['variable_dictionary'].split('§')
    replacing_words = form_values['replacing_words']
    random_domain = q.random_domain

    if template_type != 'blanks':
        answer = replace_variables_from_array(variable_dictionary, q.answer.replace('\\\\', '\\'))
    else:
        answer = get_values_from_position(template_specific, q.solution.replace('\\\\', '\\'))
        answer = replace_variables_from_array(variable_dictionary, answer)

    answer = parse_answer(answer, random_domain)
    answer = answer.replace('`', '')
    answer = answer.split('§')
    solution = str(q.question_text.replace('\\\\', '\\')) + "\\n" + str(q.solution.replace('\\\\', '\\'))
    solution = replace_variables_from_array(variable_dictionary, solution)
    solution = parse_solution(solution, random_domain)
    if len(replacing_words) > 0:
        solution = replace_words(solution, replacing_words)['sentence']
    user_answer = user_answer.split('§')  # If a string doesn't contain the character it returns a list with 1 element
    # We format both the user answer and the answer the same way.
    user_answer = [after_equal_sign(x) for x in user_answer]  # Only get the values after last equal sign.
    user_answer = calculate_array(user_answer, random_domain)
    answer = [after_equal_sign(x) for x in answer]
    answer = calculate_array(answer, random_domain)
    answer_text = "\\text{Du har svart }" + '\\text{ og }'.join(user_answer) + \
                      "\\text{. Det er feil! Svaret er: }" + '\\text{ og }'.join(answer)

    correct_answer = check_answer(user_answer, answer, template_type)  # Check if the user answered correctly.

    if correct_answer:
        answer_text = "\\text{Du har svart riktig!}"

    solution = solution.replace('+-', '-')
    solution = solution.replace('--', '+')
    answer_text = latex_exceptions(answer_text)
    context_dict = {'title': "Oppgavegen", 'answer': str(answer_text),
                    'solution': solution, 'user_won': correct_answer}
    return context_dict



def submit_template(template, user, update):
    """Submits or updates a template to the database (depending on if update is true or not)"""
    #taglist = validate_tags(template.tags)
    if update:
        q = Template.objects.get(pk=template.pk)
        template.rating = q.rating
        template.choice_rating = q.choice_rating
        template.fill_rating = q.fill_rating
        template.times_failed = q.times_failed
        template.times_solved = q.times_solved
        template.creation_date = q.creation_date
        template.creator = q.creator
        #template.tags = q.tags.all()
        template.name = q.name
        template.difficulty = q.difficulty
    else:
        template.rating = 1200
        template.fill_rating = 1150
        template.choice_rating = 1100
        template.times_failed = 0
        template.times_solved = 0
        template.creation_date = datetime.now()
        template.creator = user
    if len(template.fill_in) > 1:
        template.fill_in_support = True
    if len(template.choices) > 1:
        template.multiple_support = True
    template.save()
    message = template_validation(template.pk)
    return message


def change_elo(template, user, user_won, type):
    """Changes the elo of both user and task depending on who won."""
    u = User.objects.get(username=user.username)
    user_rating = u.extendeduser.rating
    # Formula for elo: Rx = Rx(old) + prefactor *(W-Ex) where W=1 if wins and W=0 if x loses
    # and Ex is the expected probability that x will win.
    # Ea = (1+10^((Rb-Ra)/400))^-1
    # Eb = (1+10^((Ra-Rb)/400))^-1
    if type == 'blanks':
        template_rating = template.fill_rating
    elif type == 'multiple':
        template_rating = template.choice_rating
    else:
        template_rating = template.rating


    expected_user = (1+10**((template_rating-user_rating)/400))**(-1)
    expected_template = (1+10**((template_rating-user_rating)/400))**(-1)
    prefactor_user = 30  # This value should be adjusted according to elo of the user (lower for higher ratings..)
    prefactor_template = 16  # This value should be adjusted according to elo of the user (lower for higher ratings..)


    if user_won:
        new_user_rating = user_rating + prefactor_user*(1-expected_user)
        new_template_rating = template_rating + prefactor_template*(0-expected_template)
        template.times_solved += 1
    else:
        new_user_rating = user_rating + prefactor_user*(0-expected_user)
        new_template_rating = template_rating + prefactor_template*(1-expected_template)
        template.times_failed += 1
    user.extendeduser.rating = new_user_rating
    user.extendeduser.save()
    if type == 'blanks':
        template.fill_rating = new_template_rating
    elif type == 'multiple':
        template.choice_rating = new_template_rating
    else:
        template.rating = new_template_rating
    template.save()
    return


@Debugger
def change_level_rating(template, user, user_won, type, level_id):
    """Changes the elo of both user and task depending on who won."""
    u = User.objects.get(username=user.username)
    level = Level.objects.get(pk=level_id)
    user_progress = UserLevelProgress.objects.get(user=u, level=level)
    user_rating = user_progress.level_rating
    # Formula for elo: Rx = Rx(old) + prefactor *(W-Ex) where W=1 if wins and W=0 if x loses
    # and Ex is the expected probability that x will win.
    # Ea = (1+10^((Rb-Ra)/400))^-1
    # Eb = (1+10^((Ra-Rb)/400))^-1
    if type == 'blanks':
        template_rating = template.fill_rating
    elif type == 'multiple':
        template_rating = template.choice_rating
    else:
        template_rating = template.rating

    expected_user = (1+10**((template_rating-user_rating)/400))**(-1)
    expected_template = (1+10**((template_rating-user_rating)/400))**(-1)
    prefactor_user = 30  # This value should be adjusted according to elo of the user (lower for higher ratings..)
    prefactor_template = 16  # This value should be adjusted according to elo of the user (lower for higher ratings..)

    if user_won:
        new_user_rating = user_rating + prefactor_user*(1-expected_user)
        new_template_rating = template_rating + prefactor_template*(0-expected_template)
        template.times_solved += 1
    else:
        new_user_rating = user_rating + prefactor_user*(0-expected_user)
        new_template_rating = template_rating + prefactor_template*(1-expected_template)
        template.times_failed += 1
    user_progress.level_rating = new_user_rating
    user_progress.save()

    if type == 'blanks':
        template.fill_rating = new_template_rating
    elif type == 'multiple':
        template.choice_rating = new_template_rating
    else:
        template.rating = new_template_rating
    template.save()
    return

def cheat_check(user_answer, disallowed):
    """Checks whether the user has used symbols/functions that are not allowed"""
    standard_disallowed = ['int', 'test', "'", '@']
    if disallowed is not None and disallowed != '':
        standard_disallowed = standard_disallowed + disallowed.split('§')
    for s in standard_disallowed:
        if s in user_answer:
            return True
    return False


def get_user_rating(user):
    """Returns the rating of the give user"""
    u = User.objects.get(username=user.username)
    rating = u.extendeduser.rating
    return rating


def latex_exceptions(string):
    """Replaces wrong latex with the proper one"""
    string = string.replace('\\tilde', '\\sim')
    return string


def calculate_progress(user, chapter):
    levels = chapter.level_order
    levels = levels.split(',')
    counter = 0
    for i in levels:
        level = Level.objects.get(pk=i)
        q = UserLevelProgress.objects.get(user=user, level=level)
        if q.star < 1:
            break
        counter += 1

    return counter


def validate_tags(tags):
    # template = Template.objects.get(pk=template_id)
    taglist = []
    for e in tags:
        if e in Tag.objects.all():
            taglist.append(e)
        else:
            tag = Tag.objects.new(name=e)
            taglist.append(tag)
    return taglist
