import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
import pymysql
import logging

app = Flask(__name__)
CORS(app)

# Enable logging
logging.basicConfig(level=logging.DEBUG)

def get_connection():
    return pymysql.connect(
        host='localhost',
        user='root',
        password='',
        database='SurveyApp',
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )

@app.route('/add_survey', methods=['POST'])
def add_survey():
    connection = get_connection()
    try:
        data = request.json
        survey_title = data.get('SurveyTitle')
        deadline = data.get('Deadline')
        time = data.get('Time')
        image = data.get('Image')  # Base64 encoded image

        if not survey_title:
            return jsonify({'error': 'SurveyTitle gereklidir'}), 400

        with connection.cursor() as cursor:
            sql = "INSERT INTO Surveys (SurveyTitle, Deadline, Time, Image) VALUES (%s, %s, %s, %s)"
            cursor.execute(sql, (survey_title, deadline, time, image))
            connection.commit()
            survey_id = cursor.lastrowid

        return jsonify({'message': 'Anket başarıyla eklendi', 'SurveyID': survey_id})
    except pymysql.MySQLError as e:
        app.logger.error('MySQL Error: %s', e)
        return jsonify({'error': 'MySQL Error: {}'.format(e)}), 500
    except Exception as e:
        app.logger.error('Error: %s', str(e))
        return jsonify({'error': str(e)}), 500
    finally:
        connection.close()


@app.route('/add_question', methods=['POST'])
def add_question():
    connection = get_connection()
    try:
        data = request.json
        survey_id = data.get('SurveyID')
        question_text = data.get('QuestionText')

        if not (survey_id and question_text):
            return jsonify({'error': 'SurveyID ve QuestionText gereklidir'}), 400

        with connection.cursor() as cursor:
            sql = "INSERT INTO Questions (SurveyID, QuestionText) VALUES (%s, %s)"
            cursor.execute(sql, (survey_id, question_text))
            connection.commit()
            question_id = cursor.lastrowid

        return jsonify({'message': 'Soru başarıyla eklendi', 'QuestionID': question_id})
    except pymysql.MySQLError as e:
        app.logger.error('MySQL Error: %s', e)
        return jsonify({'error': 'MySQL Error: {}'.format(e)}), 500
    except Exception as e:
        app.logger.error('Error: %s', str(e))
        return jsonify({'error': str(e)}), 500
    finally:
        connection.close()


@app.route('/add_option', methods=['POST'])
def add_option():
    connection = get_connection()
    try:
        data = request.json
        question_id = data.get('QuestionID')
        option_text = data.get('OptionText')

        if not (question_id and option_text):
            return jsonify({'error': 'QuestionID ve OptionText gereklidir'}), 400

        with connection.cursor() as cursor:
            sql = "INSERT INTO Options (QuestionID, OptionText) VALUES (%s, %s)"
            cursor.execute(sql, (question_id, option_text))
            connection.commit()
            option_id = cursor.lastrowid

        return jsonify({'message': 'Seçenek başarıyla eklendi', 'OptionID': option_id})
    except pymysql.MySQLError as e:
        app.logger.error('MySQL Error: %s', e)
        return jsonify({'error': 'MySQL Error: {}'.format(e)}), 500
    except Exception as e:
        app.logger.error('Error: %s', str(e))
        return jsonify({'error': str(e)}), 500
    finally:
        connection.close()


@app.route('/vote_option', methods=['POST'])
def vote_option():
    connection = get_connection()
    try:
        data = request.json
        option_id = data.get('OptionID')

        if not option_id:
            return jsonify({'error': 'OptionID gereklidir'}), 400

        with connection.cursor() as cursor:
            sql = "UPDATE Options SET Votes = Votes + 1 WHERE OptionID = %s"
            cursor.execute(sql, (option_id,))
            connection.commit()

        return jsonify({'message': 'Oy başarıyla kaydedildi'})
    except pymysql.MySQLError as e:
        app.logger.error('MySQL Error: %s', e)
        return jsonify({'error': 'MySQL Error: {}'.format(e)}), 500
    except Exception as e:
        app.logger.error('Error: %s', str(e))
        return jsonify({'error': str(e)}), 500
    finally:
        connection.close()


@app.route('/survey_results/<int:survey_id>', methods=['GET'])
def survey_results(survey_id):
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            sql = """
                SELECT q.QuestionID, q.QuestionText, o.OptionID, o.OptionText, o.Votes
                FROM Questions q
                LEFT JOIN Options o ON q.QuestionID = o.QuestionID
                WHERE q.SurveyID = %s
            """
            cursor.execute(sql, (survey_id,))
            result = cursor.fetchall()

            survey_results = {}
            for row in result:
                question_id = row['QuestionID']
                if question_id not in survey_results:
                    survey_results[question_id] = {
                        'QuestionID': question_id,
                        'QuestionText': row['QuestionText'],
                        'Options': []
                    }
                survey_results[question_id]['Options'].append({
                    'OptionID': row['OptionID'],
                    'OptionText': row['OptionText'],
                    'Votes': row['Votes']
                })

            survey_results_list = list(survey_results.values())
            app.logger.debug('Returned JSON: %s', survey_results_list)
            return jsonify(survey_results_list)
    except pymysql.MySQLError as e:
        app.logger.error('MySQL Error: %s', e)
        return jsonify({'error': 'MySQL Error: {}'.format(e)}), 500
    except Exception as e:
        app.logger.error('Error: %s', str(e))
        return jsonify({'error': str(e)}), 500
    finally:
        connection.close()


@app.route('/read_data', methods=['GET'])
def read_data():
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            sql = "SELECT * FROM Surveys"
            cursor.execute(sql)
            result = cursor.fetchall()

            for row in result:
                if isinstance(row['Deadline'], datetime.date):
                    row['Deadline'] = row['Deadline'].isoformat()
                if isinstance(row['Time'], datetime.timedelta):
                    row['Time'] = str(row['Time'])
                row['Image'] = row['Image']  # Görsellerin base64 kodlu halini alır

            return jsonify(result)
    except pymysql.MySQLError as e:
        app.logger.error('MySQL Error: %s', e)
        return jsonify({'error': 'MySQL Error: {}'.format(e)}), 500
    except Exception as e:
        app.logger.error('Error: %s', str(e))
        return jsonify({'error': str(e)}), 500
    finally:
        connection.close()


@app.route('/read_survey/<int:survey_id>', methods=['GET'])
def read_survey(survey_id):
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            sql = "SELECT * FROM Surveys WHERE SurveyID = %s"
            cursor.execute(sql, (survey_id,))
            result = cursor.fetchone()

            if isinstance(result['Deadline'], datetime.date):
                result['Deadline'] = result['Deadline'].isoformat()
            if isinstance(result['Time'], datetime.timedelta):
                result['Time'] = str(result['Time'])
            result['Image'] = result['Image']  # Görsellerin base64 kodlu halini alır

            return jsonify(result)
    except pymysql.MySQLError as e:
        app.logger.error('MySQL Error: %s', e)
        return jsonify({'error': 'MySQL Error: {}'.format(e)}), 500
    except Exception as e:
        app.logger.error('Error: %s', str(e))
        return jsonify({'error': str(e)}), 500
    finally:
        connection.close()


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
