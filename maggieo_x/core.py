import sys
from functools import partial
from enum import Enum
import logging
import os
import os.path
import pprint
import re
from purepyindi2 import device, properties, constants
from purepyindi2.messages import DefNumber, DefSwitch, DefText

from .personality import Personality
from .opentts_bridge import speak, ssml_to_wav

log = logging.getLogger(__name__)
HERE = os.path.dirname(__file__)
TAGS_RE = re.compile('<.*?>')

def drop_xml_tags(raw_xml):
  return TAGS_RE.sub('', raw_xml)

class Maggie(device.XDevice):
    personality : Personality
    speech_requests : list[str]
    default_voice : str = "coqui-tts:en_ljspeech"
    api_url : str = "http://localhost:5500/"
    cache_dir : str = os.path.join(HERE, "synthesis_cache")

    def handle_speech_text(self, existing_property, new_message):
        if 'target' in new_message and new_message['target'] != existing_property['current']:
            log.debug(f"Setting new speech text: {new_message['target']}")
            existing_property['current'] = new_message['target']
            existing_property['target'] = new_message['target']
        self.update_property(existing_property)
    
    def handle_speech_request(self, existing_property, new_message):
        log.debug(f"{new_message['request']=}")
        if new_message['request'] is constants.SwitchState.ON:
            current_text = self.properties['speech_text']['current']
            if current_text is not None and len(current_text.strip()) != 0:
                self.speech_requests.append(current_text)
                log.debug(f"Speech requested: {self.properties['speech_text']['current']}")
        self.update_property(existing_property)  # ensure the request switch turns back off at the client

    def reaction_handler(self, existing_property, new_message, element_name, transition, utterance_choices):
        if transition.compare(new_message[element_name]):
            log.debug(f"Submitting reaction for {element_name} change to {new_message[element_name]}")
            self.speech_request.append(choice(utterance_choices))
        else:
            log.debug(f"Got {new_message=} but {transition=} did not match")

    def setup(self):
        while self.client.status is not constants.ConnectionStatus.CONNECTED:
            log.info("Waiting for connection...")
            time.sleep(1)
        log.debug(f"Caching synthesis output to {self.cache_dir}")
        os.makedirs(self.cache_dir, exist_ok=True)
        self.personality = Personality.from_path(os.path.join(HERE, 'default.xml'))
        self.speech_requests = []
        for reaction in self.personality.reactions:
            cleaned_indi_id = reaction.indi_id.replace('.', '__')
            # sv = properties.SwitchVector(
            #     name=cleaned_indi_id,
            #     rule=constants.SwitchRule.ONE_OF_MANY,
            #     perm=constants.PropertyPerm.READ_WRITE,
            # )
            device_name, property_name, element_name = reaction.indi_id.split('.')
            self.client.get_properties(reaction.indi_id)
            for t in reaction.transitions:
                # switch_element_base_name = ""
                # if t.op is not None:
                #     switch_element_base_name += t.op.value + "_"
                #     if isinstance(t.value, Enum):
                #         value = t.value.value
                #     else:
                #         value = t.value
                #     switch_element_base_name += value
                # else:
                #     switch_element_base_name = "any"
                
                # self.client.register_callback(
                #     partial(self.reaction_handler, element_name=element_name, transition=t, utterance_choices=reaction.transitions[t]),
                #     device_name=device_name,
                #     property_name=property_name
                # )
                for idx, utterance in enumerate(reaction.transitions[t]):
                    log.debug(f"{reaction.indi_id}: {t}: {utterance}")
                    result = ssml_to_wav(utterance, self.default_voice, self.api_url, self.cache_dir)
                    log.debug(f"Saved to {result}")
                #     element_name = f"{t.op.value}_{t.value.value}"
                #     sv.add_element(DefSwitch(name=f"{element_name}_{idx:02}", _value=constants.SwitchState.OFF))
            # log.debug(f"{sv}")
            # self.add_property(sv, callback=self.handle_toggle)

        speech_text = properties.TextVector(name="speech_text")
        speech_text.add_element(DefText(
            name="current",
            _value=None,
        ))
        speech_text.add_element(DefText(
            name="target",
            _value=None,
        ))
        self.add_property(speech_text, callback=self.handle_speech_text)

        speech_request = properties.SwitchVector(
            name="speak",
            rule=constants.SwitchRule.ANY_OF_MANY,
        )
        speech_request.add_element(DefSwitch(name="request", _value=constants.SwitchState.OFF))
        self.add_property(speech_request, callback=self.handle_speech_request)

        # nv = properties.NumberVector(name='uptime')
        # nv.add_element(DefNumber(
        #     name='uptime_sec', label='Uptime', format='%3.1f',
        #     min=0, max=1_000_000, step=1, _value=0.0
        # ))
        # self.add_property(nv)
        log.debug("Set up complete")

    def loop(self):
        # uptime_prop = self.properties['uptime']
        # uptime_prop['uptime_sec'].value += 1
        # self.update_property(uptime_prop)
        # log.debug(f"Current uptime: {uptime_prop}")
        while len(self.speech_requests):
            req_text = self.speech_requests.pop(0)
            log.debug(f"Speaking: {req_text}")
            speak(req_text, self.default_voice, self.api_url, self.cache_dir)
            log.debug("Speech complete")
                


def main():
    if '-v' in sys.argv:
        logging.basicConfig(level=logging.DEBUG)
        # logging.getLogger('maggieo_x').setLevel(logging.DEBUG)
    app = Maggie(name="maggieo_x")
    app.main()