import requests
import os
from dotenv import load_dotenv
from terminaltables import AsciiTable


def predict_rub_salary(vacancy):
    start_salary, finally_salary = vacancy['salary']['from'], vacancy['salary']['to']

    if all([start_salary, finally_salary]):
        return (start_salary + finally_salary) / 2
    if start_salary:
        return start_salary * 1.2
    return finally_salary * 0.8


def get_vacancies(language, pages, per_page):
    url = f'https://api.hh.ru/vacancies'
    vacancies = []

    for page in range(pages):
        headers = {'User-Agent': 'HH-User-Agent'}
        params = {
            'text': f'Программист {language}',
            'area': 1,
            'page': page,
            'per_page': per_page,
            'currency': 'RUR',
            'date_from': '2023-06-08T21:17:21+0400',

        }

        response = requests.get(url, params=params, headers=headers)
        vacancies.append(response.json())
    return vacancies


def get_professional_statistics(list_replies, language):
    vacancy_count = 0
    average_salaries = []
    statistic_vacancy = {language: {}}
    statistic_vacancy[language].setdefault('vacancies_found', list_replies[0]['found'])

    for reply in list_replies:
        for vacancy in reply['items']:
            if vacancy['salary'] and vacancy['salary']['currency'] == 'RUR':
                vacancy_count += 1
                average_salaries.append(predict_rub_salary(vacancy))

    statistic_vacancy[language].setdefault('average_salary', int(sum(average_salaries) / len(average_salaries)))
    statistic_vacancy[language].setdefault('vacancies_processed', vacancy_count)
    return statistic_vacancy


def get_statistic_vacancies_hh(page=20, vacancies_count=100):
    languages = [
        'Python',
        'Java',
        'Javascript',
        'Typescript',
        'Go',
        'C++',
    ]

    statistic_vacancies = {}

    for language in languages:
        vacancies = get_vacancies(language, page, vacancies_count)
        statistic_vacancies.update(get_professional_statistics(vacancies, language))
    return statistic_vacancies


def predict_rub_salary_for_sj(vac):
    start_salary, finally_salary = vac['payment_from'], vac['payment_to']
    if all([start_salary, finally_salary]):
        return (start_salary + finally_salary) / 2
    if start_salary:
        return start_salary * 1.2
    return finally_salary * 0.8


def get_vacancies_super_job(pages, vacancies_count):
    load_dotenv('TOKEN.env')
    token = os.environ['SJ_TOKEN']
    languages = [
        'Python',
        'Java',
        'Javascript',
        'Typescript',
        'Go',
        'C++',
    ]

    statistic_vacancies = {}

    for language in languages:
        vacancies = get_vacancies_sj(language, token, pages, vacancies_count)
        statistic_vacancies.update(statistic_vacancies_sj(vacancies, language))
    return statistic_vacancies


def get_vacancies_sj(language, token, pages=10, vacancies_count=100):
    replies = []

    for page in range(pages):
        url = '	https://api.superjob.ru/2.0/vacancies/'
        headers = {'X-Api-App-Id': token}
        profession_name = f'{language} Программист'

        params = {
            'keyword': profession_name,
            'town': 'Москва',
            'payment_from': 50000,
            'page': page,
            'count': vacancies_count
        }

        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        if not response.json()['objects']:
            break

        replies.append(response.json())
    return replies


def statistic_vacancies_sj(replies, language):
    statistic_vacancies = {language: {}}
    statistic_vacancies[language].setdefault('vacancies_found', replies[0]['total'])
    vacancies_processed = 0
    average_salary = []

    for reply in replies:
        for vacancy in reply['objects']:
            salary = predict_rub_salary_for_sj(vacancy)
            if salary:
                vacancies_processed += 1
                average_salary.append(salary)

    statistic_vacancies[language].setdefault('vacancies_processed', vacancies_processed)
    statistic_vacancies[language].setdefault('average_salary', int(sum(average_salary) / len(average_salary)))
    return statistic_vacancies


def get_table_statistic_sj(page, vacancies_count):
    sj_statistic = get_vacancies_super_job(page, vacancies_count)

    title = 'SuperJob Moscow'
    table_data = [['Язык программирования', 'Вакансий найдено', 'Вакансий обработано', 'Средняя зарплата']]
    for language in sj_statistic:
        table_data.append(
            [language,
             sj_statistic[language]['vacancies_found'],
             sj_statistic[language]['vacancies_processed'],
             sj_statistic[language]['average_salary']
             ])

    table = AsciiTable(table_data, title)
    print(table.table)


def get_table_statistic_hh(page, vacancies_count):
    hh_statistic = get_statistic_vacancies_hh(page, vacancies_count)

    title = 'HeadHunter Moscow'
    table_data = [['Язык программирования', 'Вакансий найдено', 'Вакансий обработано', 'Средняя зарплата']]
    for language in hh_statistic:
        table_data.append(
            [language,
             hh_statistic[language]['vacancies_found'],
             hh_statistic[language]['vacancies_processed'],
             hh_statistic[language]['average_salary']
             ])

    table = AsciiTable(table_data, title)
    print(table.table)


def main():
    get_table_statistic_hh(20, 100)
    get_table_statistic_sj(5, 100)


if __name__ == '__main__':
    main()
