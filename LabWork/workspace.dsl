workspace {
    name "Coin keeper"
    description "Моделирование архитектуры сервиса ведения бюджета"
    
    model {
        user = person "Пользователь" {
            description "Пользователь сервиса ведения бюджета"
        }

        coin_keeper = softwareSystem "Сервис ведения бюджета" {
            description "Онлайн сервис для управления финансами"
            user -> this "Использует"

            client_mobile_app = container "Мобильное приложение" {
                description "Интерфейс для пользователей сервиса ведения бюджета"
                technology "React Native"
                user -> this "Работает через"
            }

            api = container "API" {
                description "Backend API для управления пользователями и финансами"
                technology "Spring Boot"
                client_mobile_app -> this "Использует"
            }

            user_service = container "User Service" {
                description "Сервис для управления пользователями"
                technology "Spring Boot"
                api -> this "Вызывает"
            }

            finance_service = container "Finance Service" {
                description "Сервис для управления финансами"
                technology "Spring Boot"
                api -> this "Вызывает"
            }

            user_db = container "База данных пользователей" {
                description "Хранение данных пользователей"
                technology "PostgreSQL"
                user_service -> this "Читает и записывает"
            }

            finance_db = container "База данных финансов" {
                description "Хранение информации о финансах"
                technology "PostgreSQL"
                finance_service -> this "Читает и записывает"
            }
        }
    }

    views {
        themes default

        systemLandscape "SystemLandscape"{
            include *
            autoLayout lr
        }

        systemContext coin_keeper "Context" {
            include *
            autoLayout
        }

        container coin_keeper "Containers" {
            include *
            autoLayout
        }

        

        dynamic coin_keeper "UC01" {
            autoLayout lr
            description "Тестовый сценарий"

            user -> coin_keeper.client_mobile_app "1. Клиент открывает мобильное приложение"
            coin_keeper.client_mobile_app -> coin_keeper.api "2. Мобильное приложение запрашивает данные для аутентификации клиента (login/password) и проверяет их через API"
            coin_keeper.api -> coin_keeper.user_service "3. API запрашивает данные пользователя"
            coin_keeper.api -> coin_keeper.finance_service "4. API запрашивает данные о финансах"
            coin_keeper.finance_service -> coin_keeper.finance_db "5. Finance Service читает данные из базы данных финансов"
            coin_keeper.user_service -> coin_keeper.user_db "6. User Service читает данные из базы данных пользователей"
        }
        
        styles {
            element "Person" {
                color #ffffff
                fontSize 22
                shape Person
            }
            element "Customer" {
                background #08427b
            }

            element "ExternalSystem" {
                background #c0c0c0
                color #ffffff
            }
            element "Container" {
                background #438dd5
                color #ffffff
            }
            element "WebBrowser" {
                shape WebBrowser
            }
            element "MobileApp" {
                shape MobileDevicePortrait
            }
            element "Database" {
                shape Cylinder
            }
            element "Queue" {
                shape Pipe
            }
            element "Component" {
                background #85bbf0
                color #000000
                shape Component
            }
        }
    }
}
