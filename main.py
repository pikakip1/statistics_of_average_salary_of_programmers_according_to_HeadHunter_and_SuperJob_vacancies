import requests
import os
from math import ceil
from dotenv import load_dotenv
from terminaltables import AsciiTable
from datetime import date, timedelta


def predict_rub_salary(start_salary, finally_salary):
    if all([start_salary, finally_salary]):
        return (start_salary + finally_salary) / 2
    if start_salary:
        return start_salary * 1.2
    return finally_salary * 0.8


def get_statistic_vacancy_hh(vacancies_on_the_page, vacancy):
    url = f'https://api.hh.ru/vacancies'
    date_start = date.today() - timedelta(days=31)
    moscow_code = 1

    vacancies = []
    page, end_page = 0, 1

    while page != end_page + 1:
        headers = {'User-Agent': 'HH-User-Agent'}
        params = {
            'text': f'Программист {vacancy}',
            'area': moscow_code,
            'page': page,
            'per_page': vacancies_on_the_page,
            'currency': 'RUR',
            'date_from': date_start,
        }
        response = requests.get(url, params=params, headers=headers)
        reply_hh = response.json()
        if not page:
            end_page = reply_hh['pages']
        page += 1
        vacancies.append(reply_hh)

    return vacancies


def create_statistic_vacancies_hh(all_vacancies_specialty):
    average_salaries = []
    for jobs_on_one_page in all_vacancies_specialty:
        if not jobs_on_one_page.get('items'):
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


def get_statistic_vacancies_sj(vacancy, vacancies_on_the_page, token):
    payment_from = 50000
    vacancies = []
    page, end_page = 0, 1

    while page < end_page:
        url = '	https://api.superjob.ru/2.0/vacancies/'
        headers = {'X-Api-App-Id': token}
        profession_name = f'{vacancy} Программист'
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

        if not page:
            end_page = ceil(one_page_vacancies['total'] / 100)
        page += 1

        vacancies.append(one_page_vacancies)

    return vacancies


def create_statistic_vacancy_sj(all_vacancies_specialty):
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


def get_table_statistic(vacancies_statistic, company):
    title = f'{company} Moscow'
    header = ['Язык программирования', 'Вакансий найдено', 'Вакансий обработано', 'Средняя зарплата']
    table_statistic = [header]

    for vacancy in vacancies_statistic:
        string_table = [
            vacancy,
            vacancies_statistic[vacancy]['vacancies_found'],
            vacancies_statistic[vacancy]['vacancies_processed'],
            vacancies_statistic[vacancy]['average_salary']
        ]

        table_statistic.append(string_table)

    table = AsciiTable(table_statistic, title)
    return table


if __name__ == '__main__':
    load_dotenv('TOKEN.env')
    sj_token = os.environ['SJ_TOKEN']

    languages = [
        'Python',
        'Java',
        'Javascript',
        'Typescript',
        'Go',
        'C++',
    ]

    hh_statistics = {}
    sj_statistics = {}
    count_vacations_in_page = 100

    for language in languages:
        hh_vacancies = get_statistic_vacancy_hh(count_vacations_in_page, language)
        hh_statistics[language] = create_statistic_vacancies_hh(hh_vacancies)

        sj_vacancies = get_statistic_vacancies_sj(language, count_vacations_in_page, sj_token)
        sj_statistics[language] = create_statistic_vacancy_sj(sj_vacancies)

    hh_table_statistic = get_table_statistic(hh_statistics, 'HeadHunter')
    sj_table_statistic = get_table_statistic(sj_statistics, 'SuperJob')

    print(hh_table_statistic.table)
    print(sj_table_statistic.table)
