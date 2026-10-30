(() => {
  const microphoneSoundThreshold = 0.001;

  const profileDefaults = () => ({
    district: null,
    land_acres: null,
    ownership: null,
    crops: [],
    season: null,
    risk_type: null,
    irrigation_type: null,
    has_water_source: null,
    availed_drip_subsidy_last_3_years: null,
    requested_equipment: null,
    equipment_cost_inr: null,
    has_soil_health_card: null,
    soil_deficiencies: [],
    is_income_tax_payee: null,
    is_institutional_landholder: null,
    is_constitutional_post_holder: null,
    is_government_employee: null,
  });

  function makeElement(tag, className, text) {
    const element = document.createElement(tag);
    if (className) element.className = className;
    if (text !== undefined) element.textContent = text;
    return element;
  }

  function postJson(path, payload) {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 50000);
    return fetch(path, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
      signal: controller.signal,
    }).then(async response => {
      const data = await response.json();
      const requestId = response.headers.get('X-Request-ID');
      if (!response.ok) {
        const reference = requestId ? ` (reference: ${requestId})` : '';
        const error = new Error(
          `${data.error || `Request failed (${response.status}).`}${reference}`,
        );
        error.status = response.status;
        throw error;
      }
      if (requestId) data.requestId = requestId;
      return data;
    }).catch(error => {
      if (controller.signal.aborted) {
        throw new Error('The request took too long. Check your connection and try again.');
      }
      throw error;
    }).finally(() => clearTimeout(timeout));
  }

  function schemeCard(result, lang) {
    const demo = result.is_demo;
    const ineligible = result.status === 'INELIGIBLE';
    const conditional = result.status === 'CONDITIONALLY_ELIGIBLE';
    const informational = result.status === 'INFORMATIONAL';
    const tone = demo ? 'amber' : ineligible ? 'rose' : conditional || informational ? 'blue' : 'emerald';
    const styles = {
      amber: { border: 'border-amber-500/70', badge: 'bg-amber-950 text-amber-300 border-amber-800', summary: 'text-amber-200' },
      rose: { border: 'border-rose-500/70', badge: 'bg-rose-950 text-rose-300 border-rose-800', summary: 'text-rose-200' },
      blue: { border: 'border-blue-500/70', badge: 'bg-blue-950 text-blue-300 border-blue-800', summary: 'text-blue-200' },
      emerald: { border: 'border-emerald-500/70', badge: 'bg-emerald-950 text-emerald-300 border-emerald-800', summary: 'text-emerald-200' },
    }[tone];
    const card = makeElement('section', `p-4 bg-slate-900 border-2 ${styles.border} rounded-2xl space-y-2`);
    const header = makeElement('div', 'flex justify-between items-start gap-3');
    const title = makeElement('h3', 'font-bold text-sm text-white',
      `${lang === 'kn' ? result.scheme_name_kn : result.scheme_name_en}${demo ? ' [DEMO / TEST CASE]' : ''}`);
    const badge = makeElement('span', `px-2 py-0.5 rounded ${styles.badge} border text-[10px] font-bold shrink-0`,
      result.status.replaceAll('_', ' '));
    header.append(title, badge);
    card.append(header);

    const summary = lang === 'kn' ? result.benefit_summary_kn : result.benefit_summary_en;
    card.appendChild(makeElement('p', `text-xs ${styles.summary} font-semibold`, summary));

    if (result.missing_information?.length) {
      card.appendChild(makeElement('p', 'text-[11px] text-blue-200',
        `${lang === 'kn' ? 'ಮತ್ತಷ್ಟು ಮಾಹಿತಿ ಬೇಕು' : 'Information still needed'}: ${result.missing_information.join(', ')}`));
    }

    for (const [label, items] of [
      [lang === 'kn' ? 'ಕಾರಣಗಳು' : 'Reasons', result.disqualification_reasons],
      [lang === 'kn' ? 'ದಾಖಲೆಗಳು' : 'Documents to prepare',
        (result.required_documents || []).map(doc => lang === 'kn' ? doc.name_kn : doc.name_en)],
      [lang === 'kn' ? 'ನಿಯಮ ಪರಿಶೀಲನೆ' : 'Rule audit', result.audit_trail],
    ]) {
      if (!items?.length) continue;
      const details = makeElement('details', 'text-[11px] text-slate-400');
      details.appendChild(makeElement('summary', 'cursor-pointer', label));
      const list = makeElement('ul', 'list-disc list-inside mt-1 space-y-1');
      items.forEach(item => list.appendChild(makeElement('li', '', item)));
      details.appendChild(list);
      card.appendChild(details);
    }

    const disclaimer = demo
      ? (lang === 'kn' ? result.disclaimer_kn : result.disclaimer_en)
      : (lang === 'kn'
        ? 'ಇದು ಅಧಿಕೃತ ಅರ್ಹತಾ ನಿರ್ಧಾರವಲ್ಲ. ಪ್ರಸ್ತುತ ನಿಯಮಗಳು ಮತ್ತು ಅರ್ಜಿ ಸ್ಥಿತಿಯನ್ನು ಸಂಬಂಧಿತ ಇಲಾಖೆಯಲ್ಲಿ ದೃಢಪಡಿಸಿ.'
        : result.disclaimer_en);
    if (disclaimer) card.appendChild(makeElement('p', 'text-[10px] text-slate-500', disclaimer));

    if (result.last_researched) {
      card.appendChild(makeElement(
        'p',
        'text-[10px] text-slate-500',
        `${lang === 'kn' ? 'ಮೂಲಗಳನ್ನು ಪರಿಶೀಲಿಸಿದ ದಿನಾಂಕ' : 'Sources checked'}: ${result.last_researched}`,
      ));
    }
    if (Array.isArray(result.sources) && result.sources.length) {
      const sourceList = makeElement('div', 'flex flex-wrap gap-x-3 gap-y-1 text-[11px]');
      result.sources.forEach(source => {
        if (typeof source.url !== 'string' || !source.url.startsWith('https://')) return;
        const link = makeElement(
          'a',
          'text-emerald-300 underline underline-offset-2 hover:text-emerald-200',
          source.label,
        );
        link.href = source.url;
        link.target = '_blank';
        link.rel = 'noopener noreferrer';
        sourceList.appendChild(link);
      });
      if (sourceList.childElementCount) card.appendChild(sourceList);
    }
    return card;
  }

  if (document.getElementById('chat-input-form')) {
    let profile = profileDefaults();
    farmerProfile = profile;
    let busy = false;
    let voiceStarting = false;
    let recorder = null;
    let mediaStream = null;
    let voiceTimeout = null;
    let recordingInterval = null;
    let audioLevelInterval = null;
    let recordingStartedAt = null;
    let audioContext = null;
    let audioAnalyser = null;
    let preferredAudioInputId = localStorage.getItem('krishi_audio_input') || '';
    let audioInputDevices = [];
    const stream = document.getElementById('chat-stream');
    const input = document.getElementById('user-text-input');
    const micButton = document.getElementById('mic-trigger-btn');
    const micModal = document.getElementById('waveform-modal');
    const audioInputControl = document.getElementById('audio-input-control');
    const audioInputSelect = document.getElementById('audio-input-select');
    const audioInputLabel = document.getElementById('audio-input-label');
    const micIcon = document.getElementById('mic-icon');
    const serviceStatus = document.getElementById('service-status');
    const serviceStatusText = document.getElementById('service-status-text');
    const loadingSpinner = document.getElementById('loading-spinner');
    const form = document.getElementById('chat-input-form');
    const submitButton = form.querySelector('button[type="submit"]');

    function setServiceStatus(text, loading = false) {
      serviceStatusText.textContent = text;
      loadingSpinner.classList.toggle('hidden', !loading);
      serviceStatus.setAttribute('aria-busy', String(loading));
    }

    async function refreshAudioInputs() {
      if (!navigator.mediaDevices?.enumerateDevices || !audioInputSelect) return;
      try {
        const devices = (await navigator.mediaDevices.enumerateDevices())
          .filter(device => device.kind === 'audioinput');
        audioInputDevices = devices;
        audioInputSelect.replaceChildren();
        audioInputLabel.textContent = currentLanguage === 'kn'
          ? 'ಇನ್‌ಪುಟ್ ಮೈಕ್'
          : 'Input microphone';
        devices.forEach((device, index) => {
          const option = document.createElement('option');
          option.value = device.deviceId;
          option.textContent = device.label
            || (currentLanguage === 'kn' ? `ಮೈಕ್ರೊಫೋನ್ ${index + 1}` : `Microphone ${index + 1}`);
          audioInputSelect.appendChild(option);
        });
        const preferredExists = devices.some(device => device.deviceId === preferredAudioInputId);
        if (!preferredExists) preferredAudioInputId = '';
        if (preferredAudioInputId) audioInputSelect.value = preferredAudioInputId;
        audioInputControl.classList.toggle('hidden', devices.length < 2);
      } catch (error) {
        console.warn('[voice] input device enumeration failed', { message: error.message });
      }
    }

    function microphoneSilenceMessage() {
      const selectedLabel = audioInputDevices.find(device =>
        device.deviceId === preferredAudioInputId)?.label
        || audioInputSelect?.selectedOptions?.[0]?.textContent
        || (currentLanguage === 'kn' ? 'ಆಯ್ಕೆ ಮಾಡಿದ ಮೈಕ್' : 'the selected microphone');
      const alternative = audioInputDevices.find(device =>
        device.deviceId !== preferredAudioInputId
        && /microphone array|microphone \(/i.test(device.label));
      const alternativeLabel = alternative?.label;
      if (currentLanguage === 'kn') {
        return alternativeLabel
          ? `"${selectedLabel}" ನಲ್ಲಿ ಧ್ವನಿ ಕೇಳಿಸಲಿಲ್ಲ. "ಇನ್‌ಪುಟ್ ಮೈಕ್" ನಲ್ಲಿ "${alternativeLabel}" ಆಯ್ಕೆಮಾಡಿ ಮತ್ತೆ ಪ್ರಯತ್ನಿಸಿ.`
          : `"${selectedLabel}" ನಲ್ಲಿ ಧ್ವನಿ ಕೇಳಿಸಲಿಲ್ಲ. "ಇನ್‌ಪುಟ್ ಮೈಕ್" ನಲ್ಲಿ ಬೇರೆ ಮೈಕ್ ಆಯ್ಕೆಮಾಡಿ ಮತ್ತೆ ಪ್ರಯತ್ನಿಸಿ.`;
      }
      return alternativeLabel
        ? `No sound was detected from "${selectedLabel}". Choose "${alternativeLabel}" in Input microphone and try again.`
        : `No sound was detected from "${selectedLabel}". Choose another input in Input microphone and try again.`;
    }

    function selectAlternativeMicrophone() {
      const alternatives = audioInputDevices.filter(device =>
        device.deviceId && device.deviceId !== preferredAudioInputId);
      const alternative = alternatives.find(device => /microphone array/i.test(device.label))
        || alternatives.find(device => /microphone/i.test(device.label))
        || alternatives[0];
      if (!alternative) return false;
      preferredAudioInputId = alternative.deviceId;
      if (preferredAudioInputId) {
        localStorage.setItem('krishi_audio_input', preferredAudioInputId);
      }
      if (audioInputSelect) audioInputSelect.value = preferredAudioInputId;
      return true;
    }

    function renderMessage(sender, text, evaluations = []) {
      const row = makeElement('div', sender === 'user'
        ? 'flex items-start justify-end gap-3 text-sm'
        : 'flex items-start gap-4 text-sm');
      row.dataset.chatMessage = 'true';
      row.dataset.chatRole = sender === 'user' ? 'user' : 'assistant';
      const avatar = makeElement('div', sender === 'user'
        ? 'w-9 h-9 rounded-xl bg-slate-800 flex items-center justify-center text-white shrink-0 mt-0.5'
        : 'w-10 h-10 rounded-2xl bg-gradient-to-tr from-emerald-600 to-teal-500 flex items-center justify-center text-white shrink-0 shadow-md',
      sender === 'user' ? 'person' : 'smart_toy');
      avatar.classList.add('material-symbols-outlined');
      const bubble = makeElement(sender === 'user' ? 'p' : 'div', sender === 'user'
        ? 'bg-emerald-600 text-white rounded-3xl rounded-tr-sm px-5 py-3.5 max-w-[85%] shadow-md text-xs sm:text-sm whitespace-pre-wrap'
        : 'space-y-3 bg-[#151E2E] border border-slate-800/80 rounded-3xl rounded-tl-sm p-5 max-w-[90%] shadow-md text-slate-200',
      text);
      bubble.dataset.chatText = text;
      if (sender === 'user') row.append(bubble, avatar);
      else {
        row.append(avatar, bubble);
        evaluations.forEach(result => bubble.appendChild(schemeCard(result, currentLanguage)));
      }
      stream.appendChild(row);
      stream.scrollTop = stream.scrollHeight;
      return bubble;
    }

    function recentChatHistory() {
      return [...stream.querySelectorAll('[data-chat-message]')]
        .slice(-8)
        .map(row => ({
          role: row.dataset.chatRole,
          content: row.querySelector('[data-chat-text]')?.dataset.chatText || '',
        }));
    }

    function playGeneratedReply(bubble, result) {
      if (!result.audio || !result.mime_type) return false;
      try {
        const audioBytes = Uint8Array.from(
          atob(result.audio),
          character => character.charCodeAt(0),
        );
        const audioUrl = URL.createObjectURL(
          new Blob([audioBytes], { type: result.mime_type }),
        );
        const player = makeElement('audio', 'w-full mt-2');
        player.controls = true;
        player.src = audioUrl;
        player.addEventListener('ended', () => {
          URL.revokeObjectURL(audioUrl);
          setServiceStatus(result.model_mode);
        }, { once: true });
        player.addEventListener('error', () => {
          URL.revokeObjectURL(audioUrl);
          setServiceStatus(currentLanguage === 'kn'
            ? 'ಧ್ವನಿ ಪ್ಲೇ ಆಗಲಿಲ್ಲ. ಕೇಳಲು ಆಡಿಯೊ ನಿಯಂತ್ರಣ ಒತ್ತಿ.'
            : 'Audio could not play. Use the audio controls to retry.');
        }, { once: true });
        bubble.appendChild(player);
        setServiceStatus(
          currentLanguage === 'kn' ? 'ಉತ್ತರಿಸುತ್ತಿದೆ…' : 'Responding…',
          true,
        );
        player.play().catch(() => setServiceStatus(currentLanguage === 'kn'
          ? 'ಉತ್ತರ ಸಿದ್ಧವಾಗಿದೆ. ಕೇಳಲು ಆಡಿಯೊ ನಿಯಂತ್ರಣ ಒತ್ತಿ.'
          : 'Reply ready. Press the audio controls to hear it.'));
        return true;
      } catch (error) {
        console.error('[chat] audio playback setup failed', { message: error.message });
        return false;
      }
    }

    async function processFarmerQuery(message) {
      const text = message.trim();
      if (!text || busy) return;
      busy = true;
      const history = recentChatHistory();
      renderMessage('user', text);
      submitButton.disabled = true;
      submitButton.classList.add('opacity-50', 'cursor-wait');
      setServiceStatus(
        currentLanguage === 'kn' ? 'ಪರಿಶೀಲಿಸಲಾಗುತ್ತಿದೆ…' : 'Thinking…',
        true,
      );
      try {
        const result = await postJson('/api/chat', {
          message: text,
          language: currentLanguage,
          profile,
          history,
        });
        profile = result.profile;
        farmerProfile = profile;
        const replyBubble = renderMessage(
          'bot',
          result.reply,
          result.show_evaluations ? result.evaluations : [],
        );
        setServiceStatus(result.model_mode);
        updateProfileBar();
        if (!playGeneratedReply(replyBubble, result)) {
          speakReply(result.reply, () => setServiceStatus(result.model_mode));
        }
      } catch (error) {
        renderMessage('bot', `${currentLanguage === 'kn' ? 'ದೋಷ' : 'Error'}: ${error.message}`);
        setServiceStatus(
          currentLanguage === 'kn' ? 'ಸೇವೆ ಲಭ್ಯವಿಲ್ಲ' : `Service unavailable: ${error.message}`,
        );
      } finally {
        busy = false;
        submitButton.disabled = false;
        submitButton.classList.remove('opacity-50', 'cursor-wait');
      }
    }

    function speakReply(text, onComplete) {
      if (!('speechSynthesis' in window) || !text) {
        onComplete?.();
        return;
      }
      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = currentLanguage === 'kn' ? 'kn-IN' : 'en-IN';
      utterance.rate = 0.92;
      const languagePrefix = currentLanguage === 'kn' ? 'kn' : 'en';
      const voice = window.speechSynthesis.getVoices()
        .find(candidate => candidate.lang.toLowerCase().startsWith(languagePrefix));
      if (voice) utterance.voice = voice;
      else if (currentLanguage === 'kn') {
        setServiceStatus('ಕನ್ನಡ ಧ್ವನಿ ಲಭ್ಯವಿಲ್ಲ. ಬರಹದ ಉತ್ತರವನ್ನು ಓದಬಹುದು.');
        onComplete?.();
        return;
      }
      setServiceStatus(
        currentLanguage === 'kn' ? 'ಉತ್ತರಿಸುತ್ತಿದೆ…' : 'Responding…',
        true,
      );
      utterance.onend = () => onComplete?.();
      utterance.onerror = () => onComplete?.();
      window.speechSynthesis.speak(utterance);
    }

    function updateProfileBar() {
      document.getElementById('pill-district').textContent = profile.district || '—';
      document.getElementById('pill-land').textContent = profile.land_acres === null
        ? '—'
        : `${profile.land_acres}${currentLanguage === 'kn' ? ' ಎಕರೆ' : ' Acres'}`;
      document.getElementById('pill-crop').textContent = profile.crops.join(', ') || '—';
      document.getElementById('pill-status').textContent =
        profile.district || profile.land_acres !== null || profile.crops.length
          ? (currentLanguage === 'kn' ? 'ಪೂರ್ಣವಲ್ಲ' : 'Incomplete')
          : (currentLanguage === 'kn' ? 'ವಿವರಗಳಿಲ್ಲ' : 'No details');
    }

    function clearProfile() {
      profile = profileDefaults();
      farmerProfile = profile;
      stream.querySelectorAll('[data-chat-message="true"]').forEach(message => message.remove());
      updateProfileBar();
      setServiceStatus('');
    }

    function resetVoice() {
      clearTimeout(voiceTimeout);
      voiceTimeout = null;
      clearInterval(recordingInterval);
      recordingInterval = null;
      clearInterval(audioLevelInterval);
      audioLevelInterval = null;
      audioAnalyser = null;
      if (audioContext) {
        audioContext.close().catch(error => {
          console.warn('[voice] audio context close failed', { message: error.message });
        });
        audioContext = null;
      }
      recordingStartedAt = null;
      if (mediaStream) mediaStream.getTracks().forEach(track => track.stop());
      recorder = mediaStream = null;
      micModal.classList.add('hidden');
      micButton.classList.remove('bg-red-600', 'pulsing-ring');
      micButton.classList.add('bg-gradient-to-tr', 'from-emerald-600', 'to-teal-500');
      micButton.disabled = false;
      micIcon.textContent = 'mic';
    }

    function stopVoiceRecording(activeRecorder, reason, startedAt) {
      if (activeRecorder?.state !== 'recording') return;
      clearTimeout(voiceTimeout);
      voiceTimeout = null;
      clearInterval(recordingInterval);
      recordingInterval = null;
      console.info('[voice] recording stop requested', {
        reason,
        recordingDurationMs: startedAt ? Date.now() - startedAt : null,
      });
      if (reason === 'max_duration') {
        setServiceStatus(currentLanguage === 'kn'
          ? 'ಗರಿಷ್ಠ ಸಮಯ ಮುಗಿದಿದೆ. ಧ್ವನಿಯನ್ನು ಕಳುಹಿಸಲಾಗುತ್ತಿದೆ…'
          : 'Recording limit reached. Sending your audio…', true);
      }
      activeRecorder.stop();
    }

    async function blobToBase64(blob) {
      const bytes = new Uint8Array(await blob.arrayBuffer());
      let binary = '';
      for (let i = 0; i < bytes.length; i += 0x8000) {
        binary += String.fromCharCode(...bytes.subarray(i, Math.min(i + 0x8000, bytes.length)));
      }
      return btoa(binary);
    }

    async function processVoiceClip(blob, recordingDurationMs) {
      if (busy) return;
      busy = true;
      submitButton.disabled = true;
      micButton.disabled = true;
      submitButton.classList.add('opacity-50', 'cursor-wait');
      setServiceStatus(
        currentLanguage === 'kn' ? 'ಧ್ವನಿಯನ್ನು ಪ್ರಕ್ರಿಯೆಗೊಳಿಸಲಾಗುತ್ತಿದೆ…' : 'Processing your voice…',
        true,
      );
      try {
        const mimeType = blob.type.split(';')[0].toLowerCase();
        console.info('[voice] upload started', {
          mimeType,
          audioBytes: blob.size,
          recordingDurationMs,
        });
        const result = await postJson('/api/voice-turn', {
          audio: await blobToBase64(blob),
          mime_type: mimeType,
          recording_duration_ms: recordingDurationMs,
          language: currentLanguage,
          profile,
          history: recentChatHistory(),
        });
        console.info('[voice] turn completed', {
          requestId: result.requestId,
          transcriptChars: result.transcript.length,
          replyChars: result.reply.length,
          audioBase64Chars: result.audio.length,
        });
        setServiceStatus(
          currentLanguage === 'kn' ? 'ಉತ್ತರ ಸಿದ್ಧಪಡಿಸಲಾಗುತ್ತಿದೆ…' : 'Preparing your reply…',
          true,
        );
        profile = result.profile;
        farmerProfile = profile;
        renderMessage('user', result.transcript);
        const replyBubble = renderMessage(
          'bot',
          result.reply,
          result.show_evaluations ? result.evaluations : [],
        );
        updateProfileBar();

        const audioBytes = Uint8Array.from(atob(result.audio), character => character.charCodeAt(0));
        const audioUrl = URL.createObjectURL(new Blob([audioBytes], { type: result.mime_type }));
        const player = makeElement('audio', 'w-full mt-2');
        player.controls = true;
        player.src = audioUrl;
        player.addEventListener('ended', () => URL.revokeObjectURL(audioUrl), { once: true });
        player.addEventListener('error', () => {
          URL.revokeObjectURL(audioUrl);
          setServiceStatus(currentLanguage === 'kn'
            ? 'ಆಡಿಯೊ ಪ್ಲೇ ಆಗಲಿಲ್ಲ. ಮೇಲಿನ ನಿಯಂತ್ರಣವನ್ನು ಬಳಸಿ.'
            : 'Audio could not play. Use the audio controls to retry.');
        }, { once: true });
        replyBubble.appendChild(player);
        setServiceStatus(result.model_mode, true);
        try {
          await player.play();
        } catch {
          setServiceStatus(currentLanguage === 'kn'
            ? 'ಉತ್ತರ ಸಿದ್ಧವಾಗಿದೆ. ಕೇಳಲು ಆಡಿಯೊ ನಿಯಂತ್ರಣವನ್ನು ಒತ್ತಿ.'
            : 'Reply ready. Press the audio controls to hear it.');
        }
        player.addEventListener('ended', () => setServiceStatus(result.model_mode), { once: true });
      } catch (error) {
        console.error('[voice] turn failed', { message: error.message });
        if (error.status === 422 && selectAlternativeMicrophone()) {
          const nextInputLabel = audioInputDevices.find(device =>
            device.deviceId === preferredAudioInputId)?.label;
          setServiceStatus(currentLanguage === 'kn'
            ? `ಮಾತು ಗುರುತಿಸಲಾಗಲಿಲ್ಲ. "${nextInputLabel}" ಆಯ್ಕೆ ಮಾಡಿದೆ; ಮತ್ತೆ ಮಾತನಾಡಿ ಪ್ರಯತ್ನಿಸಿ.`
            : `No speech was recognized. Switched to "${nextInputLabel}". Try speaking again.`);
        } else {
          setServiceStatus(error.message || 'Voice chat failed. Please try again.');
        }
      } finally {
        busy = false;
        micButton.disabled = false;
        submitButton.disabled = false;
        submitButton.classList.remove('opacity-50', 'cursor-wait');
      }
    }

    async function startVoice() {
      if (busy || voiceStarting) return;
      if (!navigator.mediaDevices?.getUserMedia) {
        setServiceStatus(currentLanguage === 'kn'
          ? 'ಮೈಕ್‌ಗೆ ಸುರಕ್ಷಿತ HTTPS ಅಥವಾ localhost ಅಗತ್ಯ.'
          : 'Microphone needs HTTPS or localhost. Type your question instead.');
        return;
      }
      if (typeof MediaRecorder === 'undefined') {
        setServiceStatus(currentLanguage === 'kn'
          ? 'ಈ ಬ್ರೌಸರ್‌ನಲ್ಲಿ ಆಡಿಯೊ ದಾಖಲಿಸುವಿಕೆ ಲಭ್ಯವಿಲ್ಲ.'
          : 'Audio recording is not supported in this browser. Try a current version of Chrome or Edge.');
        return;
      }
      voiceStarting = true;
      micButton.disabled = true;
      try {
        const permissionStatus = await navigator.permissions?.query({ name: 'microphone' })
          .catch(() => null);
        if (permissionStatus?.state === 'denied') {
          const error = new Error('Microphone permission was denied.');
          error.name = 'NotAllowedError';
          throw error;
        }
        setServiceStatus(currentLanguage === 'kn'
          ? 'ಮೈಕ್ರೊಫೋನ್ ಅನುಮತಿಗಾಗಿ ಕಾಯಲಾಗುತ್ತಿದೆ…'
          : 'Waiting for microphone permission…', true);
        const audioConstraints = {
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: false,
          autoGainControl: true,
        };
        if (preferredAudioInputId) {
          audioConstraints.deviceId = { exact: preferredAudioInputId };
        }
        const streamRequest = navigator.mediaDevices.getUserMedia({ audio: audioConstraints });
        let permissionTimedOut = false;
        let permissionTimeout;
        streamRequest.then(stream => {
          if (permissionTimedOut) stream.getTracks().forEach(track => track.stop());
        }, () => {});
        try {
          mediaStream = await Promise.race([
            streamRequest,
            new Promise((resolve, reject) => {
              permissionTimeout = setTimeout(() => {
                permissionTimedOut = true;
                const error = new Error('Microphone permission request timed out.');
                error.name = 'MicrophoneTimeoutError';
                reject(error);
              }, 12000);
            }),
          ]);
        } finally {
          clearTimeout(permissionTimeout);
        }
        await refreshAudioInputs();
        const microphoneTrack = mediaStream.getAudioTracks()[0];
        const microphoneSettings = microphoneTrack?.getSettings?.() || {};
        console.info('[voice] microphone track ready', {
          input: microphoneTrack?.label || 'unknown',
          sampleRate: microphoneSettings.sampleRate || 'unknown',
          channelCount: microphoneSettings.channelCount || 'unknown',
          noiseSuppression: microphoneSettings.noiseSuppression ?? 'unknown',
          autoGainControl: microphoneSettings.autoGainControl ?? 'unknown',
          echoCancellation: microphoneSettings.echoCancellation ?? 'unknown',
        });
        const mimeType = typeof MediaRecorder.isTypeSupported === 'function'
          ? [
            'audio/webm;codecs=opus',
            'audio/ogg;codecs=opus',
            'audio/mp4',
          ].find(type => MediaRecorder.isTypeSupported(type))
          : undefined;
        const AudioContextConstructor = window.AudioContext || window.webkitAudioContext;
        let peakInputLevel = 0;
        if (AudioContextConstructor) {
          try {
            audioContext = new AudioContextConstructor();
            const source = audioContext.createMediaStreamSource(mediaStream);
            audioAnalyser = audioContext.createAnalyser();
            audioAnalyser.fftSize = 1024;
            source.connect(audioAnalyser);
            await audioContext.resume();
          } catch (error) {
            console.warn('[voice] microphone level monitor unavailable', {
              message: error.message,
            });
            audioAnalyser = null;
          }
        }
        recorder = mimeType
          ? new MediaRecorder(mediaStream, { mimeType })
          : new MediaRecorder(mediaStream);
        const activeRecorder = recorder;
        const recordedChunks = [];
        const selectedInputLabel = microphoneTrack?.label
          || audioInputDevices.find(device => device.deviceId === preferredAudioInputId)?.label
          || audioInputSelect?.selectedOptions?.[0]?.textContent
          || 'default microphone';
        activeRecorder.ondataavailable = event => {
          if (event.data.size) {
            recordedChunks.push(event.data);
          }
        };
        activeRecorder.onerror = event => {
          resetVoice();
          const message = event.error?.message || 'Could not record microphone audio.';
          console.error('[voice] recording failed', { message });
          setServiceStatus(message);
        };
        activeRecorder.onstop = () => {
          const blob = new Blob(recordedChunks, { type: activeRecorder.mimeType || 'audio/webm' });
          const recordingDurationMs = recordingStartedAt ? Date.now() - recordingStartedAt : 0;
          console.info('[voice] recording stopped', {
            mimeType: blob.type,
            audioBytes: blob.size,
            recordingDurationMs,
            chunks: recordedChunks.length,
            peakInputLevel: Number(peakInputLevel.toFixed(4)),
            input: selectedInputLabel,
          });
          resetVoice();
          if (!blob.size) {
            setServiceStatus(currentLanguage === 'kn'
              ? 'ಧ್ವನಿ ದಾಖಲಾಗಲಿಲ್ಲ. ಮತ್ತೆ ಪ್ರಯತ್ನಿಸಿ.'
              : 'No audio was recorded. Please try again.');
            return;
          }
          if (audioAnalyser && peakInputLevel < microphoneSoundThreshold) {
            console.warn('[voice] input meter detected no sound; sending recording for transcription', {
              input: selectedInputLabel,
              audioBytes: blob.size,
            });
          }
          processVoiceClip(blob, recordingDurationMs);
        };
        recordingStartedAt = Date.now();
        activeRecorder.start(250);
        voiceStarting = false;
        micButton.disabled = false;
        console.info('[voice] recording started', { mimeType: activeRecorder.mimeType });
        let recordingSeconds = 0;
        micModal.classList.remove('hidden');
        micButton.classList.remove('from-emerald-600', 'to-teal-500');
        micButton.classList.add('bg-red-600', 'pulsing-ring');
        micIcon.textContent = 'stop';
        setServiceStatus(currentLanguage === 'kn'
          ? 'ಮಾತನಾಡಿ, ಮುಗಿದಾಗ ಮೈಕ್ ಒತ್ತಿ ಕಳುಹಿಸಿ (ಗರಿಷ್ಠ 25 ಸೆಕೆಂಡು).'
          : 'Speak, then tap the mic to send (up to 25 seconds).');
        const micStatusLabel = document.getElementById('mic-status-label');
        const micSubtextLabel = document.getElementById('mic-subtext-label');
        let soundDetected = false;
        const samples = audioAnalyser ? new Uint8Array(audioAnalyser.fftSize) : null;
        if (audioAnalyser && samples) {
          audioLevelInterval = setInterval(() => {
            audioAnalyser.getByteTimeDomainData(samples);
            let sumSquares = 0;
            for (const sample of samples) {
              const normalized = (sample - 128) / 128;
              sumSquares += normalized * normalized;
            }
            const level = Math.sqrt(sumSquares / samples.length);
            peakInputLevel = Math.max(peakInputLevel, level);
            if (level >= microphoneSoundThreshold) {
              soundDetected = true;
              if (micStatusLabel) {
                micStatusLabel.textContent = currentLanguage === 'kn'
                  ? 'ಧ್ವನಿ ಕೇಳಿಸುತ್ತಿದೆ…'
                  : 'Microphone is picking up sound…';
              }
              if (micSubtextLabel) {
                micSubtextLabel.textContent = currentLanguage === 'kn'
                  ? 'ಮುಗಿದಾಗ ಮೈಕ್ ಒತ್ತಿ ಕಳುಹಿಸಿ'
                  : 'Tap the microphone when you are done to send';
              }
            } else if (!soundDetected && Date.now() - recordingStartedAt > 3000) {
              if (micStatusLabel) {
                micStatusLabel.textContent = currentLanguage === 'kn'
                  ? 'ಧ್ವನಿ ಕೇಳಿಸುತ್ತಿಲ್ಲ'
                  : 'No sound detected yet';
              }
              if (micSubtextLabel) {
                micSubtextLabel.textContent = microphoneSilenceMessage();
              }
            }
          }, 120);
        }
        recordingInterval = setInterval(() => {
          recordingSeconds = Math.floor((Date.now() - recordingStartedAt) / 1000);
          if (recordingSeconds >= 25) {
            stopVoiceRecording(activeRecorder, 'max_duration', recordingStartedAt);
            return;
          }
          setServiceStatus(currentLanguage === 'kn'
            ? `ದಾಖಲಿಸಲಾಗುತ್ತಿದೆ… ${recordingSeconds} ಸೆಕೆಂಡು`
            : `Recording… ${recordingSeconds}s`);
        }, 1000);
        voiceTimeout = setTimeout(() => {
          stopVoiceRecording(activeRecorder, 'max_duration', recordingStartedAt);
        }, 25000);
      } catch (error) {
        voiceStarting = false;
        resetVoice();
        console.error('[voice] microphone setup failed', { message: error.message });
        const microphoneErrorMessages = {
          NotAllowedError: currentLanguage === 'kn'
            ? 'ಮೈಕ್ರೊಫೋನ್ ಅನುಮತಿ ನಿರಾಕರಿಸಲಾಗಿದೆ. ಬ್ರೌಸರ್ ಸೈಟ್ ಸೆಟ್ಟಿಂಗ್‌ಗಳಲ್ಲಿ ಮೈಕ್ ಅನುಮತಿಸಿ.'
            : 'Microphone permission was denied. Allow microphone access in your browser site settings.',
          NotFoundError: currentLanguage === 'kn'
            ? 'ಮೈಕ್ರೊಫೋನ್ ಕಂಡುಬಂದಿಲ್ಲ. ಮೈಕ್ ಸಂಪರ್ಕಿಸಿ ಮತ್ತೆ ಪ್ರಯತ್ನಿಸಿ.'
            : 'No microphone was found. Connect a microphone and try again.',
          NotReadableError: currentLanguage === 'kn'
            ? 'ಮೈಕ್ರೊಫೋನ್ ಬಳಸಲಾಗುತ್ತಿಲ್ಲ. ಬೇರೆ ಆಪ್ ಮೈಕ್ ಬಳಸುತ್ತಿದೆಯೇ ನೋಡಿ.'
            : 'The microphone is unavailable. Check whether another app is using it.',
          MicrophoneTimeoutError: currentLanguage === 'kn'
            ? 'ಮೈಕ್ ಅನುಮತಿ ಸಿಗಲಿಲ್ಲ. ವಿಳಾಸ ಪಟ್ಟಿಯಲ್ಲಿರುವ ಸೈಟ್ ಸೆಟ್ಟಿಂಗ್‌ಗಳಲ್ಲಿ ಮೈಕ್ರೊಫೋನ್ ಅನುಮತಿಸಿ.'
            : 'Microphone permission did not respond. Allow microphone access in the site settings beside your browser address bar.',
        };
        setServiceStatus(
          microphoneErrorMessages[error.name] || error.message || 'Could not start voice input.',
        );
      }
    }

    audioInputSelect?.addEventListener('change', () => {
      preferredAudioInputId = audioInputSelect.value;
      if (preferredAudioInputId) localStorage.setItem('krishi_audio_input', preferredAudioInputId);
      else localStorage.removeItem('krishi_audio_input');
      setServiceStatus(currentLanguage === 'kn'
        ? 'ಆಯ್ಕೆ ಮಾಡಿದ ಮೈಕ್ ಮುಂದಿನ ದಾಖಲಿಸುವಿಕೆಗೆ ಬಳಸಲಾಗುತ್ತದೆ.'
        : 'Selected microphone will be used for the next recording.');
    });

    document.addEventListener('click', event => {
      if (event.target.closest('#mic-trigger-btn')) {
        event.preventDefault();
        event.stopImmediatePropagation();
        if (recorder?.state === 'recording') {
          stopVoiceRecording(recorder, 'manual', recordingStartedAt);
        }
        else startVoice();
      }
    }, true);

    document.getElementById('chat-lang-btn').addEventListener('click', updateProfileBar);
    document.getElementById('mobile-lang-btn').addEventListener('click', updateProfileBar);

    form.addEventListener('submit', event => {
      event.preventDefault();
      event.stopImmediatePropagation();
      const message = input.value.trim();
      if (message) {
        input.value = '';
        processFarmerQuery(message);
      }
    }, true);

    window.processFarmerQuery = processFarmerQuery;
    window.appendChatMsg = (sender, text, evaluations = []) => renderMessage(sender, text, evaluations);
    window.updateLiveProfileBar = updateProfileBar;
    window.clearActiveProfile = clearProfile;
    window.startNewChat = clearProfile;
    window.loadPersonaQuery = type => {
      const samples = {
        crop_health: currentLanguage === 'kn'
          ? 'ನನ್ನ ಬೆಳೆ ಆರೋಗ್ಯವಾಗಿದೆಯೇ ಎಂದು ಹೇಗೆ ತಿಳಿಯಲಿ?'
          : 'What should I check first if my crop looks unhealthy?',
        irrigation: currentLanguage === 'kn'
          ? 'ನನ್ನ ಹೊಲದಲ್ಲಿ ನೀರನ್ನು ಮಿತವಾಗಿ ಹೇಗೆ ಬಳಸಬಹುದು?'
          : 'How can I use water more efficiently on my farm?',
        soil: currentLanguage === 'kn'
          ? 'ನನ್ನ ಹೊಲದ ಮಣ್ಣಿನ ಗುಣಮಟ್ಟವನ್ನು ಹೇಗೆ ಸುಧಾರಿಸಬಹುದು?'
          : 'How can I improve the soil in my field?',
      };
      processFarmerQuery(samples[type] || samples.crop_health);
    };

    updateProfileBar();
    fetch('/api/health')
      .then(response => {
        if (!response.ok) throw new Error('Backend is unavailable.');
        return response.json();
      })
      .then(data => {
        setServiceStatus(`${data.model_mode} · ${data.voice_mode}`);
      })
      .catch(() => {
        setServiceStatus(currentLanguage === 'kn'
          ? 'ಹಿಂಬದಿ ಸೇವೆ ಲಭ್ಯವಿಲ್ಲ — python -m backend.web_server ಚಾಲನೆ ಮಾಡಿ.'
          : 'Backend unavailable — start it with: python -m backend.web_server');
      });
  }

  if (document.getElementById('form-results-container')) {
    const resultsContainer = document.getElementById('form-results-container');
    const status = makeElement('p', 'text-xs text-slate-400');
    resultsContainer.appendChild(status);

    const evaluateForm = async () => {
      const dist = document.getElementById('form-dist').value;
      const acres = Number(document.getElementById('form-land-slider').value);
      const crop = document.getElementById('form-crop').value;
      const cropIndex = document.getElementById('form-crop').selectedIndex;
      const irrigation = document.getElementById('form-irrig').value;
      const calamity = document.getElementById('form-calamity').value;
      const need = document.getElementById('form-need').value;
      const ownership = document.getElementById('form-ownership')?.value || null;
      const tax = document.getElementById('form-taxpayer')?.value;
      const governmentEmployee = document.getElementById('form-government-employee')?.value;
      const institutional = document.getElementById('form-institutional')?.value;
      const constitutional = document.getElementById('form-constitutional')?.value;
      const hasSoilCard = document.getElementById('form-soil-card')?.value;
      const soilDeficiency = document.getElementById('form-soil-deficiency')?.value;
      const dripCooldown = document.getElementById('form-drip-cooldown')?.value;
      const canonicalCrop = typeof AGRO_DATA !== 'undefined'
        ? (AGRO_DATA[dist]?.cropsEn?.[cropIndex] || crop)
        : crop;
      const profile = {
        district: dist,
        land_acres: acres,
        ownership,
        crops: canonicalCrop ? [canonicalCrop] : [],
        season: document.getElementById('form-season')?.value || null,
        irrigation_type: irrigation,
        has_water_source: irrigation !== 'Rainfed',
        risk_type: calamity === 'None' ? null : calamity,
        requested_equipment: need === 'Equipment' ? 'Power Tiller' : null,
        has_soil_health_card: hasSoilCard === '' || hasSoilCard === undefined
          ? null : hasSoilCard === 'true',
        soil_deficiencies: soilDeficiency ? [soilDeficiency] : [],
        availed_drip_subsidy_last_3_years: dripCooldown === '' || dripCooldown === undefined
          ? null : dripCooldown === 'true',
        is_income_tax_payee: tax === '' ? null : tax === 'true',
        is_government_employee: governmentEmployee === '' ? null : governmentEmployee === 'true',
        is_institutional_landholder: institutional === '' ? null : institutional === 'true',
        is_constitutional_post_holder: constitutional === '' ? null : constitutional === 'true',
      };
      const button = document.getElementById('form-btn-eval');
      button.disabled = true;
      status.textContent = currentLang === 'kn' ? 'ಪರಿಶೀಲಿಸಲಾಗುತ್ತಿದೆ…' : 'Checking with the rule engine…';
      Array.from(resultsContainer.children).forEach(child => {
        if (child !== status) child.remove();
      });
      try {
        const result = await postJson('/api/evaluate', { profile });
        result.evaluations.forEach(evaluation => {
          const card = schemeCard(evaluation, currentLang);
          card.dataset.evaluation = 'true';
          resultsContainer.appendChild(card);
        });
        status.textContent = currentLang === 'kn'
          ? 'ಪ್ರಾಥಮಿಕ ಪರಿಶೀಲನೆ ಮಾತ್ರ. ಇದು ಅಧಿಕೃತ ಅನುಮೋದನೆ ಅಲ್ಲ.'
          : 'Preliminary screening only; not an official approval.';
      } catch (error) {
        status.textContent = `${currentLang === 'kn' ? 'ದೋಷ' : 'Error'}: ${error.message}`;
      } finally {
        button.disabled = false;
      }
    };
    window.triggerManualFormEval = evaluateForm;
    document.getElementById('form-btn-eval').addEventListener('click', evaluateForm);
  }
})();
