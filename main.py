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


def get_statistic_vacancies_hh(vacancies_on_the_page):
    languages = [
        'Python',
        'Java',
        'Javascript',
        'Typescript',
        'Go',
        'C++',
    ]

    vacancies_statistic = {}
    url = f'https://api.hh.ru/vacancies'
    headers = {'User-Agent': 'HH-User-Agent'}
    params = {'per_page': vacancies_on_the_page}
    pages = requests.get(url, params=params, headers=headers).json()['pages']
    date_start = date.today() - timedelta(days=31)
    moscow_code = 1

    for language in languages:
        vacancies = []
        for page in range(pages):
            headers = {'User-Agent': 'HH-User-Agent'}
            params = {
                'text': f'Программист {language}',
                'area': moscow_code,
                'page': page,
                'per_page': vacancies_on_the_page,
                'currency': 'RUR',
                'date_from': date_start,

            }

            response = requests.get(url, params=params, headers=headers)
            vacancies.append(response.json())
        vacancies_statistic[language] = create_statistic_vacancies_hh(vacancies)

    return vacancies_statistic


def create_statistic_vacancies_hh(all_vacancies_specialty):
    average_salaries = []

    for jobs_on_one_page in all_vacancies_specialty:
        if jobs_on_one_page.get('items') is None:
            continue
        for vacancy in jobs_on_one_page['items']:
            if not vacancy['salary'] or vacancy['salary']['currency'] != 'RUR':
                continue
            start_salary, finally_salary = vacancy['salary']['from'], vacancy['salary']['to']
            average_salary = predict_rub_salary(start_salary, finally_salary)
            average_salaries.append(average_salary)

    vacancy_statistic = {
        'vacancies_processed': len(average_salaries),
        'average_salary': int(sum(average_salaries) / (len(average_salaries) or 1)),
        'vacancies_found': all_vacancies_specialty[0]['found']
    }
    return vacancy_statistic


def get_statistic_vacancies_sj(pages, vacancies_on_the_page, token):
    languages = [
        'Python',
        'Java',
        'Javascript',
        'Typescript',
        'Go',
        'C++',
    ]
    vacancies_statistic = {}

    payment_from = 50000

    for language in languages:
        vacancies = []
        for page in range(pages):
            url = '	https://api.superjob.ru/2.0/vacancies/'
            headers = {'X-Api-App-Id': token}
            profession_name = f'{language} Программист'

            params = {
                'keyword': profession_name,
                'town': 'Москва',
                'payment_from': payment_from,
                'page': page,
                'count': vacancies_on_the_page
            }

            response = requests.get(url, headers=headers, params=params)
            one_page_vacancies = response.json()

            if not one_page_vacancies['objects']:
                break

            vacancies.append(one_page_vacancies)
        vacancies_statistic[language] = create_statistic_vacancies_sj(vacancies)

    return vacancies_statistic


def create_statistic_vacancies_sj(all_vacancies_specialty):
    average_salaries = []
    for jobs_on_one_page in all_vacancies_specialty:
        for vacancy in jobs_on_one_page['objects']:
            start_salary, finally_salary = vacancy['payment_from'], vacancy['payment_to']
            salary = predict_rub_salary(start_salary, finally_salary)
            if salary:
                average_salaries.append(salary)

    vacancies_statistic = {
        'vacancies_found': all_vacancies_specialty[0]['total'],
        'average_salary': int(sum(average_salaries) / (len(average_salaries) or 1)),
        'vacancies_processed': len(average_salaries)
    }

    return vacancies_statistic


def get_table_statistic(vacancies_statistic):
    title = 'HeadHunter Moscow'
    header = ['Язык программирования', 'Вакансий найдено', 'Вакансий обработано', 'Средняя зарплата']
    table_statistic = [header]

    for language in vacancies_statistic:
        string_table = [
            language,
            vacancies_statistic[language]['vacancies_found'],
            vacancies_statistic[language]['vacancies_processed'],
            vacancies_statistic[language]['average_salary']
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
