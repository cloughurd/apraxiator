import logging

from .speechdetection.filterbythreshold import Filterer
from .speechdetection.findendpoints import EndpointFinder
from .speechdetection.voiceactivitydetector import VoiceActivityDetector
from .wavreader.wavreader import read

class WSDCalculator():
    def __init__(self, storage):
        self.measurers = {
            'filter': Filterer(storage),
            'endpoint': EndpointFinder(storage),
            'vad': VoiceActivityDetector(storage)
        }
        self.logger = logging.getLogger(__name__)

    def calculate_wsd(self, recording, syllable_count, evaluation_id, user_id, method='endpoint'):
        """ Uses the supplied method to calculate a Word Syllable Duration (WSD) measurement.

        Parameters:
        recording (str or file object): location of recording file or the file object itself
        syllable_count (int): number of syllables in the recorded word
        evaluation_id (str): id connecting this recording to an evaluation group
        method (str): specifies which version of calculation to use, options: ['filter','endpoint','average']

        Returns:
        float: WSD measurement, average milliseconds per syllable in the recording
        """
        audio, sr = read(recording)

        m = self.measurers.get(method, None)
        # Default is to average all methods
        if m is None:
            total = 0
            for mes in self.measurers.values():
                total += mes.measure(audio, sr, evaluation_id, user_id)
            duration = total / len(self.measurers)
        else:
            duration = m.measure(audio, sr, evaluation_id, user_id)
            
        duration = float(duration)
        wsd = duration / syllable_count

        self.logger.info('[event=wsd-calculated][evaluationId=%s][duration=%s][syllableCount=%s][wsd=%s]', evaluation_id, duration, syllable_count, wsd)
        return wsd, duration
