import pymysql
import os
import logging
import pickle

from .evaluationstorage import EvaluationStorage
from .recordingstorage import RecordingStorage
from .waiverstorage import WaiverStorage
from ..models.waiver import Waiver
from ..models.attempt import Attempt
from ..models.evaluation import Evaluation
from .dbexceptions import ConnectionException, ResourceAccessException
from .storageexceptions import PermissionDeniedException

class SQLStorage(EvaluationStorage, RecordingStorage, WaiverStorage):
    def __init__(self, name='apraxiator'):
        p = os.environ.get('MYSQL_PASSWORD', None)
        self.db = pymysql.connections.Connection(user='root', password=p, database=name)
        self.logger = logging.getLogger(__name__)
        self._create_tables()
        self.logger.info('[event=sql-storage-started]')

    def is_healthy(self):
        try:
            self.db.ping()
        except Exception as e:
            self.logger.exception('[event=ping-db-error]')
            raise ConnectionException(e)

    ''' Evaluation Storage Methods '''

    def _add_evaluation(self, e):
        sql = 'INSERT INTO evaluations (evaluation_id, age, gender, impression, owner_id) VALUES (%s, %s, %s, %s, %s)'
        val = (e.id, e.age, e.gender, e.impression, e.owner_id)
        try:
            self._execute_insert_query(sql, val)
        except Exception as ex:
            self.logger.exception('[event=add-evaluation-failure][evaluationId=%s]', e.id)
            raise ResourceAccessException(e.id, ex)
        self.logger.info('[event=evaluation-added][evaluationId=%s]', e.id)

    def _update_evaluation(self, id, field, value):
        sql = 'UPDATE evaluations SET {} = %s WHERE evaluation_id = %s'.format(field)
        val = (value, id)
        try:
            self._execute_update_statement(sql, val)
        except Exception as e:
            self.logger.exception('[event=update-evaluation-failure][evaluationId=%s][updateField=%s][updateValue=%r]', id, field, value)
            raise ResourceAccessException(id, e)
        self.logger.info('[event=evaluation-updated][evaluationId=%s][updateField=%s][updateValue=%r]', id, field, value)        

    def _get_threshold(self, id):
        sql = 'SELECT ambiance_threshold FROM evaluations WHERE evaluation_id = %s'
        val = (id,)
        try:
            res = self._execute_select_query(sql, val)
        except Exception as e:
            self.logger.exception('[event=get-threshold-failure][evaluationId=%s]', id)
            raise ResourceAccessException(id, e)
        self.logger.info('[event=threshold-retrieved][evaluationId=%s][threshold=%s]', id, res[0])
        return res[0]
    
    def _add_attempt(self, a):
        sql = 'INSERT INTO attempts (attempt_id, evaluation_id, word, wsd, duration) VALUE (%s, %s, %s, %s, %s)'
        val = (a.id, a.evaluation_id, a.word, a.wsd, a.duration)
        try:
            self._execute_insert_query(sql, val)
        except Exception as e:
            self.logger.exception('[event=add-attempt-failure][evaluationId=%s][attemptId=%s]', a.evaluation_id, a.id)
            raise ResourceAccessException(a.id, e)
        self.logger.info('[event=attempt-added][evaluationId=%s][attemptId=%s]', a.evaluation_id, a.id)

    def _get_attempts(self, evaluation_id):
        sql = 'SELECT * FROM attempts WHERE evaluation_id = %s'
        val = (evaluation_id,)
        try:
            res = self._execute_select_many_query(sql, val)
        except Exception as e:
            self.logger.exception('[event=get-attempts-failure][evaluationId=%s]', evaluation_id)
            raise ResourceAccessException(evaluation_id, e)
        attempts = []
        for row in res:
            attempts.append(Attempt.from_row(row))
        self.logger.info('[event=attempts-retrieved][evaluationId=%s][attemptCount=%s]', evaluation_id, len(attempts))
        return attempts

    def _update_attempt(self, id, field, value):
        sql = 'UPDATE attempts SET {} = %s WHERE attempt_id = %s'.format(field)
        val = (value, id)
        try:
            self._execute_update_statement(sql, val)
        except Exception as e:
            self.logger.exception('[event=update-attempt-failure][attemptId=%s][updateField=%s][updateValue=%r]', id, field, value)
            raise ResourceAccessException(id, e)
        self.logger.info('[event=attempt-updated][attemptId=%s][updateField=%s][updateValue=%r]', id, field, value)  


    def _get_evaluations(self, owner_id):
        sql = 'SELECT evaluation_id, age, gender, impression, owner_id, date_created FROM evaluations WHERE owner_id = %s'
        val = (owner_id,)
        try:
            res = self._execute_select_many_query(sql, val)
        except Exception as e:
            self.logger.exception('[event=get-evaluations-failure][ownerId=%s]', owner_id)
            raise ResourceAccessException(f'evaluations for {owner_id}', e)
        evaluations = []
        for row in res:
            evaluations.append(Evaluation.from_row(row))
        self.logger.info('[event=evaluations-retrieved][ownerId=%s][evaluationCount=%s]', owner_id, len(evaluations))
        return evaluations

    def _check_is_owner(self, evaluation_id, owner_id):
        sql = 'SELECT owner_id FROM evaluations WHERE evaluation_id = %s'
        val = (evaluation_id,)
        res = self._execute_select_query(sql, val)
        if res[0] != owner_id:
            self.logger.error('[event=access-denied][evaluationId=%s][userId=%s]', evaluation_id, owner_id)
            raise PermissionDeniedException(evaluation_id, owner_id)
        else:
            self.logger.info('[event=owner-verified][evaluationId=%s][userId=%s]', evaluation_id, owner_id)

    ''' General MySQL Interaction Methods '''

    def _execute_insert_query(self, sql, val):
        self.logger.info(self._make_info_log('db-insert', sql, val))
        c = self.db.cursor()
        c.execute(sql, val)
        self.db.commit()

    def _execute_update_statement(self, sql, val):
        self.logger.info(self._make_info_log('db-update', sql, val))
        c = self.db.cursor()
        c.execute(sql, val)
        self.db.commit()
    
    def _execute_select_query(self, sql, val):
        self.logger.info(self._make_info_log('db-select', sql, val))
        c = self.db.cursor()
        c.execute(sql, val)
        return c.fetchone()

    def _execute_select_many_query(self, sql, val):
        self.logger.info(self._make_info_log('db-select-many', sql, val))
        c = self.db.cursor()
        c.execute(sql, val)
        return c.fetchall()

    ''' Recording Storage Methods '''

    def _save_recording(self, recording, attempt_id):
        sql = 'INSERT INTO recordings (attempt_id, recording) VALUE (%s, %s)'
        val = (attempt_id, recording)
        try:
            self._execute_insert_query(sql, val)
        except Exception as e:
            self.logger.exception('[event=save-recording-failure][attemptId=%s]', attempt_id)
            raise ResourceAccessException(attempt_id, e)
        self.logger.info('[event=recording-saved][attemptId=%s]', attempt_id)

    def _get_recording(self, attempt_id):
        sql = 'SELECT recording FROM recordings WHERE attempt_id = %s'
        val = (attempt_id,)
        try:
            res = self._execute_select_query(sql, val)
        except Exception as e:
            self.logger.exception('[event=get-recording-failure][attemptId=%s]', attempt_id)
            raise ResourceAccessException(attempt_id, e)
        self.logger.info('[event=recording-retrieved][attemptId=%s]', attempt_id)
        return res[0]

    ''' Waiver Storage Methods '''

    def _add_waiver(self, w):
        sql = ("INSERT INTO waivers ("
                "subject_name, subject_email, representative_name, representative_relationship,"
                "date, signer, valid, filepath, owner_id) "
                "VALUES (%s, %s, %s, %s, %s, %s, %r, %s, %s);")
        val = (w.res_name, w.res_email, w.rep_name, w.rep_relationship, w.date, w.signer, w.valid, w.filepath, w.owner_id)
        try:
            self._execute_insert_query(sql, val)
        except Exception as ex:
            self.logger.exception('[event=add-waiver-failure][subjectName=%s][subjectEmail=%s]', w.res_name, w.res_email)
            raise ResourceAccessException(None, ex)
        self.logger.info('[event=waiver-added][subjectName=%s][subjectEmail=%s]', w.res_name, w.res_email)

    def get_valid_waivers(self, res_name, res_email, user):
        sql = 'SELECT * FROM waivers WHERE subject_name = %s AND subject_email = %s AND valid = %r AND owner_id = %s;'
        val = (res_name, res_email, True, user)
        try:
            res = self._execute_select_many_query(sql, val)
        except Exception as e:
            self.logger.exception('[event=get-valid-waiver-failure][subjectName=%s][subjectEmail=%s]', res_name, res_email)
            raise ResourceAccessException(None, e)
        waivers = []
        for row in res:
            waivers.append(Waiver.from_row(row))
        self.logger.info('[event=valid-waivers-retrieved][subjectName=%s][subjectEmail=%s][waiverCount=%s]', res_name, res_email, len(waivers))
        return waivers

    def _update_waiver(self, id, field, value):
        sql = 'UPDATE waivers SET {} = %s WHERE waiver_id = %s;'.format(field)
        val = (value, id)
        try:
            self._execute_update_statement(sql, val)
        except Exception as e:
            self.logger.exception('[event=update-waiver-failure][waiverId=%s][field=%s][value=%r]',
                                  id, field, value)
            raise ResourceAccessException(None, e)
        self.logger.info('[event=waiver-updated][waiverId=%s][field=%s][value=%r]',
                         id, field, value)

    ''' Table Setup '''

    def _create_tables(self):
        create_evaluations_statement = ("CREATE TABLE IF NOT EXISTS `evaluations` ("
            "`evaluation_id` varchar(48) NOT NULL,"
            "`age` varchar(16) NOT NULL,"
            "`gender` varchar(16) NOT NULL,"
            "`impression` varchar(255) NOT NULL,"
            "`owner_id` varchar(48) NOT NULL,"
            "`ambiance_threshold` float DEFAULT NULL,"
            "`date_created` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,"
            "PRIMARY KEY (`evaluation_id`)"
            ");"
        )
        create_attempts_statement = ("CREATE TABLE IF NOT EXISTS `attempts` ("
            "`evaluation_id` varchar(48) NOT NULL,"
            "`word` varchar(48) NOT NULL,"
            "`attempt_id` varchar(48) NOT NULL,"
            "`wsd` float NOT NULL,"
            "`duration` float NOT NULL,"
            "`include` boolean NOT NULL DEFAULT TRUE,"
            "`date_created` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,"
            "PRIMARY KEY (`attempt_id`),"
            "KEY `evaluation_id_idx` (`evaluation_id`),"
            "CONSTRAINT `evaluation_id` FOREIGN KEY (`evaluation_id`) REFERENCES `evaluations` (`evaluation_id`)"
            ");"
        )
        create_recordings_statement = ("CREATE TABLE IF NOT EXISTS `recordings` ("
            "`recording_id` int AUTO_INCREMENT NOT NULL,"
            "`attempt_id` varchar(48) NOT NULL,"
            "`date_created` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,"
            "`recording` mediumblob NOT NULL,"
            "PRIMARY KEY (`recording_id`),"
            "KEY `attempt_id_idx` (`attempt_id`),"
            "CONSTRAINT `attempt_id` FOREIGN KEY (`attempt_id`) REFERENCES `attempts` (`attempt_id`)"
            ");"
        )
        create_waivers_statement = ("CREATE TABLE IF NOT EXISTS `waivers` ("
            "`waiver_id` int AUTO_INCREMENT NOT NULL,"
            "`subject_name` varchar(255) NOT NULL,"
            "`subject_email` varchar(255) NOT NULL,"
            "`representative_name` varchar(255),"
            "`representative_relationship` varchar(255),"
            "`date` varchar(255) NOT NULL,"
            "`signer` varchar(48) NOT NULL,"
            "`valid` boolean NOT NULL DEFAULT TRUE,"
            "`filepath` varchar(255) NOT NULL,"
            "`owner_id` varchar(48) NOT NULL,"
            "PRIMARY KEY (`waiver_id`)"
            ");"
        )
        c = self.db.cursor()
        c.execute(create_evaluations_statement)
        c.execute(create_attempts_statement)
        c.execute(create_recordings_statement)
        c.execute(create_waivers_statement)

    @staticmethod
    def _make_info_log(event, sql, val):
        fmt = '[event={event}][sql={sql}][vals={vals}]'

        str_vals = []
        for v in val:
            if isinstance(v, str) or isinstance(v, float) or isinstance(v, int):
                str_vals.append(v)
            else:
                str_vals.append('nonstring')

        if sql[0] == 'I':
            sql_msg = sql.split('VALUE', 0)[0]
        elif sql[0] in 'SU':
            sql_msg = sql
        else:
            sql_msg = 'unrecognized sql'
        return fmt.format(event=event, sql=sql_msg, vals='-'.join(str_vals))