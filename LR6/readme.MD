Дополнение шестой ЛР:

17. Реализовать паттерн CQRS для одной из сущностей
18. Метод POST должен публиковать сообщение о создании в очередь kafka,
отдельный сервис должен читать сообщения и записывать их в базу

Работа должны содержать docker-compose.yml, который:
 - запускает приложение app в контейнере (собирается из dockerfile), которое
выполняет вариант задания
 - запускает базу данных PostgreSQL, MongoDB и Redis в отдельных контейнере
 - проводит первоначальную инициализацию баз данных

Вариант 12:

Бюджетирование https://about.coinkeeper.me/
Приложение должно содержать следующие данные:
 - планируемый доход
 - планируемый расход
 - пользователь

Реализовать API:
 - Создание нового пользователя
 - Поиск пользователя по логину
 - Поиск пользователя по маске имя и фамилии
 - Создать планируемый доход
 - Получить перечень планируемых доходов
 - Создать планируемый расход
 - Получить перечень планируемых расходов
