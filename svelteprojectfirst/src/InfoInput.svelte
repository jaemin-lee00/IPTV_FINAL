<script>
	import { createEventDispatcher, onMount } from 'svelte';
	import { processVoiceInput } from './services/voiceService';
	
	const dispatch = createEventDispatcher();

	let currentStep = 0;
	let userInfo = {
			name: '',
			age: '',
			sex: '',
			weight: '',
			height: '',
			sleepTime: '',
			drink: '',
			smoke: '',
			fatigue: '',
			systolicBP: '',
			diastolicBP: '',
			heartRate: '',
			walking: '',
			cholesterol: ''
	};

	// 타이핑 효과를 위한 변수들
	let displayText = "";
	let currentIndex = 0;
	let showingCursor = false;
	let errorMessage = '';

	const steps = [
			{ field: 'name', label: '성함이 어떻게 되시나요?', type: 'text', required: true },
			{ field: 'age', label: '연세가 어떻게 되시나요?', type: 'number', required: true },
			{ field: 'sex', label: '성별을 선택해 주세요', type: 'select', options: ['남자', '여자'], required: true },
			{ field: 'weight', label: '몸무게는 몇 kg이신가요?', type: 'number', step: '0.1', required: true },
			{ field: 'height', label: '키는 몇 cm이신가요?', type: 'number', step: '0.1', required: true },
			{ field: 'sleepTime', label: '하루에 몇 시간 주무시나요?', type: 'number', step: '0.5', required: true },
			{ field: 'drink', label: '술을 드시나요?', type: 'select', options: ['예', '아니오'], required: true },
			{ field: 'smoke', label: '담배를 피우시나요?', type: 'select', options: ['예', '아니오'], required: true },
			{ field: 'fatigue', label: '평소에 피로감을 느끼시나요?', type: 'select', options: ['예', '아니오'], required: true },
			{ field: ['systolicBP', 'diastolicBP'], label: '혈압은 어떻게 되시나요?', type: 'number', required: false },
			{ field: 'heartRate', label: '심장박동수는 어떻게 되시나요?', type: 'number', required: false },
			{ field: 'walking', label: '평소에 걷기 운동을 얼마나 하시나요?', type: 'select', options: ['매우 많이 걷는다', '꽤 많이 걷는다', '보통 걷는다', '조금 걷는다', '거의 걷지 않는다'], required: false },
			{ field: 'cholesterol', label: '콜레스테롤이 높다고 들어보셨나요?', type: 'select', options: ['예', '아니오'], required: false }
	];

	onMount(() => {
			startTyping();
			// 키보드 이벤트 리스너 추가
			window.addEventListener('keydown', handleKeydown);
			
			// 컴포넌트 제거 시 이벤트 리스너 정리
			return () => {
					window.removeEventListener('keydown', handleKeydown);
			}
	});

    // steps 배열이나 currentStep이 변경될 때마다 타이핑 효과 재시작
    $: if (steps[currentStep]) {
        clearTypingEffect();  // 타이핑 효과 초기화
        startTyping();
    }

    function clearTypingEffect() {
        displayText = "";
        currentIndex = 0;
        showingCursor = false;
    }

    function startTyping() {
        const text = steps[currentStep].label;
        const interval = setInterval(() => {
            if (currentIndex < text.length) {
                displayText = text.substring(0, currentIndex + 1);  // 문자열 슬라이싱 사용
                currentIndex++;
            } else {
                showingCursor = true;
                clearInterval(interval);
            }
        }, 60);

        return () => clearInterval(interval);  // 클린업 함수
    }


	function handleNext() {
			if (isValidInput()) {
					errorMessage = '';
					if (currentStep < steps.length - 1) {
							currentStep++;
					} else {
							dispatch('finish', userInfo);
					}
			}
	}

	function handleBack() {
			errorMessage = '';
			if (currentStep > 0) {
					currentStep--;
			} else {
					dispatch('goToWelcome');
			}
	}

	function handleSkip() {
			errorMessage = '';
			if (!steps[currentStep].required) {
					if (Array.isArray(steps[currentStep].field)) {
							steps[currentStep].field.forEach(field => {
									userInfo[field] = null;
							});
					} else {
							userInfo[steps[currentStep].field] = null;
					}
					if (currentStep < steps.length - 1) {
							currentStep++;
					} else {
							dispatch('finish', userInfo);
					}
			}
	}

	function isValidInput() {
			const currentStepInfo = steps[currentStep];
			
			if (currentStepInfo.field === 'walking' || currentStepInfo.field === 'cholesterol') {
					return true;
			}

			if (Array.isArray(currentStepInfo.field)) {
					const systolic = userInfo.systolicBP;
					const diastolic = userInfo.diastolicBP;
					if ((systolic && !diastolic) || (!systolic && diastolic)) {
							errorMessage = '수축기 혈압과 이완기 혈압을 모두 입력해주세요.';
							return false;
					}
					return true;
			} else {
					const value = userInfo[currentStepInfo.field];
					
					if (currentStepInfo.required && (value === '' || value === null || value === undefined)) {
							return false;
					}

					if (currentStepInfo.field === 'name') {
							if (!/^[가-힣a-zA-Z\s]+$/.test(value)) {
									errorMessage = '이름은 문자만 입력 가능합니다.';
									return false;
							}
					}

					if (currentStepInfo.type === 'number') {
							const numValue = parseFloat(value);
							if (isNaN(numValue)) {
									return false;
							}
							if (currentStepInfo.step) {
									const step = parseFloat(currentStepInfo.step);
									const remainder = (numValue / step) % 1;
									if (remainder !== 0 && Math.abs(remainder - 1) > Number.EPSILON) {
											return false;
									}
							}
					}

					if (currentStepInfo.type === 'select') {
							return currentStepInfo.options.includes(value);
					}
			}

			return true;
	}

	function typeAction(node, type) {
			node.type = type;
			return {
					update(newType) {
							node.type = newType;
					}
			};
	}

	function handleSelect(option) {
			const currentField = steps[currentStep].field;
			if (currentField === 'walking') {
					const walkingValues = {
							'매우 많이 걷는다': 10000,
							'꽤 많이 걷는다': 8000,
							'보통 걷는다': 7000,
							'조금 걷는다': 5600,
							'거의 걷지 않는다': 3000
					};
					userInfo[currentField] = walkingValues[option];
			} else {
					userInfo[currentField] = option;
			}
			userInfo = {...userInfo};
	}

	function handleInput(event) {
			if (steps[currentStep].field === 'name') {
					event.target.value = event.target.value.replace(/[^가-힣a-zA-Z\s]/g, '');
			}
	}

	let isRecording = false;
    let mediaRecorder;
    let audioChunks = [];
    let recordingStatus = '';
    let recordingTime = 0;
    let recordingTimer;

    function updateRecordingTime() {
        recordingTime++;
        recordingStatus = `녹음 중... (${recordingTime}초)`;
    }

    async function startVoiceInput() {
        if (isRecording) {
            clearInterval(recordingTimer);
            recordingStatus = '녹음 처리 중...';
            mediaRecorder.stop();
            isRecording = false;
            return;
        }

        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            isRecording = true;
            audioChunks = [];
            recordingTime = 0;
            recordingStatus = '녹음 시작...';
            errorMessage = '';

            mediaRecorder = new MediaRecorder(stream);
            mediaRecorder.ondataavailable = (event) => {
                audioChunks.push(event.data);
            };

            mediaRecorder.onstop = async () => {
                try {
                    const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
                    const currentStepInfo = steps[currentStep];
                    
                    if (!currentStepInfo) {
                        throw new Error('현재 단계 정보를 찾을 수 없습니다.');
                    }

                    recordingStatus = '음성 처리 중...';
                    const result = await processVoiceInput(
                        audioBlob,
                        currentStepInfo.label,
                        currentStepInfo.field
                    );
                    
                    if (result.success && result.processed_answer) {
                        recordingStatus = `인식된 답변: ${result.raw_text}`;
                        userInfo[currentStepInfo.field] = result.processed_answer;
                        setTimeout(() => {
                            if (isValidInput()) {
                                handleNext();
                            }
                            recordingStatus = '';
                        }, 2000);
                    } else {
                        throw new Error(result.error || '음성 처리에 실패했습니다.');
                    }
                } catch (error) {
                    console.error('Voice processing error:', error);
                    recordingStatus = '';
                    errorMessage = error.message || '음성 처리 중 오류가 발생했습니다.';
                } finally {
                    stream.getTracks().forEach(track => track.stop());
                }
            };

            mediaRecorder.start();
            recordingTimer = setInterval(updateRecordingTime, 1000);
        } catch (error) {
            console.error('Error accessing microphone:', error);
            recordingStatus = '';
            errorMessage = '마이크 접근에 실패했습니다.';
        }
    }

	// 키보드 이벤트 핸들러 추가
	function handleKeydown(event) {
		if (event.code === 'Space') {
			event.preventDefault(); // 스페이스바의 기본 동작 방지
			startVoiceInput();
		}
	}
</script>

<div class="background">
	<div class="info-input">
			<div class="question-container">
					<h2>{displayText}{#if showingCursor}<span class="cursor">_</span>{/if}</h2>
			</div>
			
			{#if errorMessage}
					<p class="error">{errorMessage}</p>
			{/if}
			
			{#if steps[currentStep].type === 'select'}
					<div class="button-group">
							{#each steps[currentStep].options as option}
									<button 
											class:selected={userInfo[steps[currentStep].field] === (steps[currentStep].field === 'walking' ? 
													Object.values({
															'매우 많이 걷는다': 10000,
															'꽤 많이 걷는다': 8000,
															'보통 걷는다': 7000,
															'조금 걷는다': 5600,
															'거의 걷지 않는다': 3000
													})[steps[currentStep].options.indexOf(option)] : option)}
											on:click={() => handleSelect(option)}
									>
											{option}
									</button>
							{/each}
					</div>
			{:else if Array.isArray(steps[currentStep].field)}
					<div class="input-group">
							<label>
									수축기 혈압:
									<input 
											type="number"
											bind:value={userInfo.systolicBP}
											required={steps[currentStep].required}
											on:input={() => userInfo = {...userInfo}}
									>
							</label>
							<label>
									이완기 혈압:
									<input 
											type="number"
											bind:value={userInfo.diastolicBP}
											required={steps[currentStep].required}
											on:input={() => userInfo = {...userInfo}}
									>
							</label>
					</div>
			{:else}
					<input 
							use:typeAction={steps[currentStep].type}
							bind:value={userInfo[steps[currentStep].field]}
							step={steps[currentStep].step}
							required={steps[currentStep].required}
							on:input={handleInput}
					>
			{/if}

			<!-- 통합된 음성 입력 UI -->
			<div class="voice-input-container">
				{#if recordingStatus}
					<div class="recording-status">
						{recordingStatus}
					</div>
				{/if}
				<button 
					class="voice-input-button" 
					class:recording={isRecording}
					on:click={startVoiceInput}
				>
					<span class="mic-icon">🎤</span>
					{isRecording ? '녹음 중지하기 (Space)' : '음성으로 답변하기 (Space)'}
				</button>
			</div>

			<div class="navigation">
					<button on:click={handleBack}>뒤로가기</button>
					{#if !steps[currentStep].required}
							<button on:click={handleSkip}>건너뛰기</button>
					{/if}
					<button on:click={handleNext}>
							{currentStep === steps.length - 1 ? '확인' : '다음'}
					</button>
			</div>
	</div>
</div>

<style>
	.background {
			background-image: url('background.png');
			background-size: cover;
			background-position: center;
			min-height: 100vh;
			width: 100%;
			position: fixed;
			top: 0;
			left: 0;
	}

	.info-input {
			display: flex;
			flex-direction: column;
			align-items: center;
			justify-content: flex-start;
			min-height: 100vh;
			padding-top: 2em;
	}

	.question-container {
			width: 100%;
			text-align: left;
			padding: 2em;
			margin-bottom: 2em;
	}

	h2 {
			position: relative;
			left: 20px;
			top: -100px;
			font-size: 5em;
			color: rgb(0, 0, 0);
			line-height: 1.3;
			font-weight: 500;
	}

	input {
			font-size: 1.2em;
			padding: 0.5em;
			margin-bottom: 1em;
			border: 1px solid #ccc;
			border-radius: 5px;
			width: 100%;
			max-width: 300px;
	}

	.button-group {
			display: flex;
			justify-content: center;
			flex-wrap: wrap;
			gap: 1em;
			margin-bottom: 1em;
	}

	.button-group button {
			font-size: 1.2em;
			padding: 0.5em 1em;
			background-color: white;
			border: 2px solid #ff9900;
			color: #ff9900;
			cursor: pointer;
			transition: all 0.3s ease;
			border-radius: 5px;
	}

	.button-group button.selected {
			background-color: #ff9900;
			color: white;
	}

	.button-group button:hover {
			background-color: #ffc400;
			color: white;
			transform: scale(1.05);
			box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
	}

	.navigation {
			display: flex;
			justify-content: space-between;
			width: 100%;
			max-width: 300px;
			gap: 1em;
	}

	.navigation button {
			font-size: 1.2em;
			padding: 0.5em 1em;
			background-color: white;
			border: 2px solid #ff9900;
			color: #ff9900;
			cursor: pointer;
			transition: all 0.3s ease;
			border-radius: 5px;
	}

	.navigation button:hover {
			background-color: #ffc400;
			color: white;
			transform: scale(1.05);
			box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
	}

	.input-group {
			display: flex;
			flex-direction: column;
			align-items: flex-start;
			margin-bottom: 1em;
			width: 100%;
			max-width: 300px;
	}

	.input-group label {
			margin-bottom: 0.5em;
			width: 100%;
			color: white;
			text-shadow: 1px 1px 3px rgba(0, 0, 0, 0.5);
	}

	.error {
			color: #ff3333;
			margin-bottom: 1em;
			text-shadow: 1px 1px 3px rgba(0, 0, 0, 0.5);
	}

	.cursor {
			animation: blink 1s infinite;
	}

	@keyframes blink {
			0% { opacity: 1; }
			50% { opacity: 0; }
			100% { opacity: 1; }
	}

	.voice-input-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        margin: 1em 0;
    }

    .voice-input-button {
        display: flex;
        align-items: center;
        gap: 8px;
        background-color: #ff4081;
        color: white;
        border: none;
        padding: 0.8em 1.5em;
        border-radius: 25px;
        cursor: pointer;
        transition: all 0.3s ease;
        font-size: 1.1em;
    }

    .mic-icon {
        font-size: 1.2em;
    }

    .voice-input-button:hover {
        background-color: #f50057;
        transform: scale(1.05);
    }

    .voice-input-button.recording {
        background-color: #f50057;
        animation: pulse 1.5s infinite;
    }

    .recording-status {
        margin: 1em 0;
        padding: 0.5em 1em;
        background-color: rgba(0, 0, 0, 0.7);
        color: white;
        border-radius: 5px;
        font-size: 1.1em;
        animation: fadeIn 0.3s ease-in-out;
    }

    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.05); }
        100% { transform: scale(1); }
    }

	@keyframes fadeIn {
		from { opacity: 0; }
		to { opacity: 1; }
	}
</style>
