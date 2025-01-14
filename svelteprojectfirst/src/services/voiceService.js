const API_URL = 'http://localhost:8000';  // API 서버 주소

export async function processVoiceInput(audioBlob, question, questionType) {
    if (!question || !questionType) {
        throw new Error('Question and questionType are required');
    }

    console.log('Processing voice input:', {
        blobSize: audioBlob.size,
        question,
        questionType
    });

    const formData = new FormData();
    formData.append('audio', audioBlob, 'voice.wav');
    formData.append('question', question);
    formData.append('question_type', questionType);

    try {
        console.log('Sending request to server...');
        const response = await fetch(`${API_URL}/process-voice`, {
            method: 'POST',
            body: formData
        });

        const result = await response.json();
        console.log('Server response:', result);

        if (!response.ok || !result.success) {
            throw new Error(result.error || 'Voice processing failed');
        }

        return result;
    } catch (error) {
        console.error('Error processing voice:', error);
        throw error;
    }
}
