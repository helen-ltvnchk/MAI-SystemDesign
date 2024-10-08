workspace {

    model {
        user = person "Пользователь" "Пользователь приложения CoinKeeper"

        coinkeeper = softwareSystem "CoinKeeper" "Приложение для управления личными финансами" {
            webApp = container "Веб-приложение" "React.js" "Предоставляет веб-интерфейс для пользователей"
            mobileApp = container "Мобильное приложение" "React Native" "Предоставляет мобильный интерфейс для пользователей"
            api = container "API" "Node.js, Express" "Обрабатывает запросы от клиентских приложений"
            database = container "База данных" "PostgreSQL" "Хранит данные о пользователях, планируемых доходах и расходах"
        }

        # Определение связей API
        user -> webApp "Использует"
        user -> mobileApp "Использует"
        webApp -> api "Отправляет запросы"
        mobileApp -> api "Отправляет запросы"
        api -> database "Читает/пишет данные"
    }

    views {
        systemContext coinkeeper "CoinKeeper_Context" {
            include *
            autolayout lr
        }

        container coinkeeper "CoinKeeper_Containers" {
            include *
            autolayout lr
        }

        dynamic coinkeeper "Create_User" "Создание нового пользователя" {
            user -> webApp "Нажимает кнопку 'Регистрация'"
            webApp -> api "Отправляет запрос на создание пользователя"
            api -> database "Сохраняет данные пользователя"
            api -> webApp "Возвращает ответ об успешном создании"
            webApp -> user "Отображает сообщение об успешной регистрации"
        }

        styles {
            element "Person" {
                background "#0a60ff"
                color "#ffffff"
                shape "Person"
            }
            element "Software System" {
                background "#1168bd"
                color "#ffffff"
            }
            element "Container" {
                background "#438dd5"
                color "#ffffff"
            }
        }
    }
}