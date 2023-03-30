from pprint import pprint

a = {
    "homeworks": [
        {
            "id": 124,
            "status": "rejected",
            "homework_name": "username__hw_python_oop.zip",
            "reviewer_comment": "Код не по PEP8, нужно исправить",
            "date_updated": "2020-02-13T16:42:47Z",
            "lesson_name": "Итоговый проект"
        },
    ],
    "current_date": 1581604970,
    "current": 34
}

# if "homeworks" and "current_date" in a:
#     print('ok')
a = a['homeworks'][0]['homework_name'].replace('username__', '').replace('.zip', '')
# a = a.replace('username__', '').replace('.zip', '')
pprint(a)
