# Smoking Detection Application

**Описание**

Это приложение предназначено для обнаружения курения с использованием камеры и обработки видео в реальном времени. Оно включает функции записи обнаруженных кадров и их отображения в удобном интерфейсе.

**Основные функции**

- Запуск и остановка видеопотока
- Сохранение обнаруженных изображений
- Отображение сохраненных изображений
- Фильтрация изображений по датам

**Датасет**
https://app.roboflow.com/dpp/cigarette-detection-bow3d/browse?queryText=&pageSize=50&startingIndex=0&browseQuery=true

Датасет включает в себя большой объём фотографий курящих людей с отмеченными сигаретами. 10% - контекст, изображения без сигарет.

**Запуск**

1. Проверьте, что есть базаданных, если нет, запустите db.py
2. Запустите приложение:
    ```sh
    python main.py
    ```

3. Используйте интерфейс для запуска и остановки видеопотока, а также для просмотра и фильтрации изображений.

**Демонстрация**

<video width="600" controls>
  <source src="[https://github.com/AnnVarlamova/diploma/blob/main/demo.mp4]" type="video/mp4">
</video>

**Алгоритм**
![Alg Screenshot](https://github.com/AnnVarlamova/diploma/blob/main/alg.png)
![App Screenshot](https://github.com/AnnVarlamova/diploma/blob/main/app.png)

