import requests
import os
from dotenv import load_dotenv
from terminaltables import AsciiTable
from datetime import date, timedelta


def predict_rub_salary(start_salary, finally_salary):
    if all([start_salary, finally_salary]):
        return (start_salary + finally_salary) / 2
    if start_salary:
        return start_salary * 1.2
    return finally_salary * 0.8


def get_vacancies(language, pages, per_page):

    url = f'https://api.hh.ru/vacancies'
    vacancies = []
    date_start = date.today() - timedelta(days=31)
    moscow_code = 1

    for page in range(pages):
        headers = {'User-Agent': 'HH-User-Agent'}
        params = {
            'text': f'Программист {language}',
            'area': moscow_code,
            'page': page,
            'per_page': per_page,
            'currency': 'RUR',
            'date_from': date_start,

        }

        response = requests.get(url, params=params, headers=headers)
        vacancies.append(response.json())
    return vacancies


def get_professional_statistics(hh_replies, language):
    vacancy_count = 0
    average_salaries = []

    for hh_reply in hh_replies:
        for vacancy in hh_reply['items']:
            if vacancy['salary'] and vacancy['salary']['currency'] == 'RUR':
                vacancy_count += 1
                start_salary, finally_salary = vacancy['salary']['from'], vacancy['salary']['to']
                average_salary = predict_rub_salary(start_salary, finally_salary)
                average_salaries.append(average_salary)

    vacancy_statistic = {
        language: {
            'vacancies_processed': vacancy_count,
            'average_salary': int(sum(average_salaries) / len(average_salaries)),
            'vacancies_found': hh_replies[0]['found']
        }
    }
    return vacancy_statistic


def get_statistic_vacancies_hh(page, vacancies_count):
    languages = [
        'Python',
        'Java',
        'Javascript',
        'Typescript',
        'Go',
        'C++',
    ]

    vacancies_statistic = {}

    for language in languages:
        vacancies = get_vacancies(language, page, vacancies_count)
        vacancies_statistic.update(get_professional_statistics(vacancies, language))
    return vacancies_statistic


def get_vacancies_super_job(pages, vacancies_count, token):
    languages = [
        'Python',
        'Java',
        'Javascript',
        'Typescript',
        'Go',
        'C++',
    ]

    vacancies_statistic = {}

    for language in languages:
        vacancies = get_vacancies_sj(language, token, pages, vacancies_count)
        vacancies_statistic.update(get_statistic_vacancies_sj(vacancies, language))
    return vacancies_statistic


def get_vacancies_sj(language, token, pages, vacancies_count):
    sj_replies = []
    payment_from = 50000

    for page in range(pages):
        url = '	https://api.superjob.ru/2.0/vacancies/'
        headers = {'X-Api-App-Id': token}
        profession_name = f'{language} Программист'

        params = {
            'keyword': profession_name,
            'town': 'Москва',
            'payment_from': payment_from,
            'page': page,
            'count': vacancies_count
        }

        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        sj_vacancies = response.json()

        if not sj_vacancies['objects']:
            break

        sj_replies.append(sj_vacancies)
    return sj_replies


def get_statistic_vacancies_sj(sj_replies, language):
    vacancies_processed = 0
    average_salary = []
    for sj_reply in sj_replies:
        for vacancy in sj_reply['objects']:
            start_salary, finally_salary = vacancy['payment_from'], vacancy['payment_to']
            salary = predict_rub_salary(start_salary, finally_salary)
            if salary:
                vacancies_processed += 1
                average_salary.append(salary)

    vacancies_statistic = {
        language: {
            'vacancies_found': sj_replies[0]['total'],
            'average_salary': int(sum(average_salary) / len(average_salary)),
            'vacancies_processed': vacancies_processed
        }
    }

    return vacancies_statistic


def get_table_statistic_sj(sj_statistic):
    title = 'SuperJob Moscow'
    header = ['Язык программирования', 'Вакансий найдено', 'Вакансий обработано', 'Средняя зарплата']
    table_statistic = [header]

    for language in sj_statistic:
        string_table = [
            language,
            sj_statistic[language]['vacancies_found'],
            sj_statistic[language]['vacancies_processed'],
            sj_statistic[language]['average_salary']
        ]

        table_statistic.append(string_table)

    table = AsciiTable(table_statistic, title)
    return table


def get_table_statistic_hh(hh_statistic):
    title = 'HeadHunter Moscow'
    header = ['Язык программирования', 'Вакансий найдено', 'Вакансий обработано', 'Средняя зарплата']
    table_statistic = [header]

    for language in hh_statistic:
        string_table = [
            language,
            hh_statistic[language]['vacancies_found'],
            hh_statistic[language]['vacancies_processed'],
            hh_statistic[language]['average_salary']
        ]

        table_statistic.append(string_table)

    table = AsciiTable(table_statistic, title)
    return table


def main():
    load_dotenv('TOKEN.env')
    sj_token = os.environ['SJ_TOKEN']

    hh_vacancies_on_the_page = 100
    sj_pages_check, sj_vacancies_on_the_page = 5, 100

    hh_statistic = get_statistic_vacancies_hh(hh_vacancies_on_the_page)
    hh_table_statistic = get_table_statistic(hh_statistic)

    sj_statistic = get_statistic_vacancies_sj(sj_pages_check, sj_vacancies_on_the_page, sj_token)
    sj_table_statistic = get_table_statistic(sj_statistic)

    return hh_table_statistic.table, sj_table_statistic.table


if __name__ == '__main__':
    tables = main()
    print(tables[0])
    print(tables[1])