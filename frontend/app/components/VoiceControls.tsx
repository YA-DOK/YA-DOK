

"use client";

import { useEffect, useRef, useState } from "react";

type VoiceStatus =
  | "idle"
  | "listening"
  | "processing"
  | "speaking"
  | "error";

type SpeechRecognitionResult = {
  isFinal: boolean;
  0: { transcript: string };
};

type SpeechRecognitionEvent = {
  resultIndex: number;
  results: ArrayLike<SpeechRecognitionResult>;
};

type SpeechRecognitionLike = {
  lang: string;
  continuous: boolean;
  interimResults: boolean;
  onresult: ((event: SpeechRecognitionEvent) => void) | null;
  onerror: ((event: { error: string }) => void) | null;
  onend: (() => void) | null;
  start: () => void;
  stop: () => void;
  abort: () => void;
};

type SpeechRecognitionConstructor = new () => SpeechRecognitionLike;

declare global {
  interface Window {
    SpeechRecognition?: SpeechRecognitionConstructor;
    webkitSpeechRecognition?: SpeechRecognitionConstructor;
  }
}

export default function VoiceControls() {
  const [status, setStatus] = useState<VoiceStatus>("idle");
  const [transcript, setTranscript] = useState("");
  const [audioUrl, setAudioUrl] = useState("");
  const [errorMessage, setErrorMessage] = useState("");
  const [ttsText, setTtsText] = useState("");
const [isSpeaking, setIsSpeaking] = useState(false);

const speakText = () => {
  if (!ttsText.trim()) {
    setErrorMessage("Please enter text to speak.");
    return;
  }

  if (!("speechSynthesis" in window)) {
    setErrorMessage("Text-to-Speech is not supported in this browser.");
    return;
  }

  window.speechSynthesis.cancel();

  const utterance = new SpeechSynthesisUtterance(ttsText);
  utterance.lang = "ar-EG";
  utterance.rate = 0.9;
  utterance.pitch = 1;

  utterance.onstart = () => setIsSpeaking(true);

  utterance.onend = () => setIsSpeaking(false);

utterance.onerror = (event) => {
  setIsSpeaking(false);
  setErrorMessage(`Speech error: ${event.error}`);
  console.error("TTS Error:", event.error);
};

  window.speechSynthesis.speak(utterance);
};

const stopSpeaking = () => {
  window.speechSynthesis.cancel();
  setIsSpeaking(false);
};
  const [transcriptionSupported, setTranscriptionSupported] =
    useState(true);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const recognitionRef = useRef<SpeechRecognitionLike | null>(null);
  const transcriptRef = useRef("");

  useEffect(() => {
    return () => {
      recognitionRef.current?.abort();
      streamRef.current?.getTracks().forEach((track) => track.stop());

      if (audioUrl) {
        URL.revokeObjectURL(audioUrl);
      }
    };
  }, [audioUrl]);

  const startListening = async () => {
    try {
      setErrorMessage("");
      setTranscript("");
      transcriptRef.current = "";
      audioChunksRef.current = [];

      if (audioUrl) {
        URL.revokeObjectURL(audioUrl);
        setAudioUrl("");
      }

      if (!navigator.mediaDevices?.getUserMedia) {
        throw new Error(
          "Microphone access is unavailable. Use localhost or HTTPS."
        );
      }

      const stream = await navigator.mediaDevices.getUserMedia({
        audio: true,
      });

      streamRef.current = stream;

      const recorder = new MediaRecorder(stream);
      mediaRecorderRef.current = recorder;

      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      recorder.onstop = () => {
        const audioBlob = new Blob(audioChunksRef.current, {
          type: recorder.mimeType || "audio/webm",
        });

        setAudioUrl(URL.createObjectURL(audioBlob));

        stream.getTracks().forEach((track) => track.stop());
        streamRef.current = null;

        setStatus("processing");
      };

      recorder.start();

      const Recognition =
        window.SpeechRecognition ||
        window.webkitSpeechRecognition;

      if (!Recognition) {
        setTranscriptionSupported(false);
        setErrorMessage(
          "Recording works, but speech-to-text is not supported in this browser."
        );
        setStatus("listening");
        return;
      }

      setTranscriptionSupported(true);

      const recognition = new Recognition();
      recognition.lang = "ar-EG";
      recognition.continuous = true;
      recognition.interimResults = true;

      recognition.onresult = (event) => {
        let currentTranscript = "";

        for (let i = 0; i < event.results.length; i++) {
          currentTranscript += event.results[i][0].transcript + " ";
        }

        const cleanTranscript = currentTranscript.trim();
        transcriptRef.current = cleanTranscript;
        setTranscript(cleanTranscript);
      };

      recognition.onerror = (event) => {
        if (event.error === "not-allowed") {
          setErrorMessage(
            "Speech recognition permission was denied. You can still stop and keep your recording."
          );
        } else if (event.error !== "no-speech") {
          setErrorMessage(
            `Speech recognition error: ${event.error}. Your recording can still be saved.`
          );
        }
      };

      recognitionRef.current = recognition;

      try {
        recognition.start();
      } catch {
        setErrorMessage(
          "Speech recognition could not start. Audio recording is still available."
        );
      }

      setStatus("listening");
    } catch (error) {
      streamRef.current?.getTracks().forEach((track) => track.stop());
      streamRef.current = null;

      setStatus("error");

      if (
        error instanceof DOMException &&
        error.name === "NotAllowedError"
      ) {
        setErrorMessage("Microphone permission was denied.");
      } else {
        setErrorMessage(
          error instanceof Error
            ? error.message
            : "Unable to access the microphone."
        );
      }
    }
  };

  const stopListening = () => {
    recognitionRef.current?.stop();
    recognitionRef.current = null;

    if (mediaRecorderRef.current?.state === "recording") {
      mediaRecorderRef.current.stop();
    } else {
      streamRef.current?.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
      setStatus("processing");
    }
  };

  const returnToText = () => {
    recognitionRef.current?.abort();
    recognitionRef.current = null;

    if (mediaRecorderRef.current?.state === "recording") {
      mediaRecorderRef.current.stop();
    }

    streamRef.current?.getTracks().forEach((track) => track.stop());
    streamRef.current = null;

    if (audioUrl) {
      URL.revokeObjectURL(audioUrl);
    }

    setAudioUrl("");
    setTranscript("");
    transcriptRef.current = "";
    setErrorMessage("");
    setStatus("idle");
  };

  return (
    <section className="w-full max-w-md rounded-2xl border border-gray-200 bg-white p-5 shadow-sm">
      <h2 className="mb-4 text-lg font-semibold text-gray-900">
        Voice Interaction
      </h2>

      <div className="mb-4 flex items-center gap-2">
        <span
          className={`h-3 w-3 rounded-full ${
            status === "listening"
              ? "bg-red-500"
              : status === "error"
                ? "bg-red-700"
                : status === "speaking"
                  ? "bg-green-500"
                  : "bg-gray-400"
          }`}
        />

        <p className="text-sm text-gray-600">
          {status === "processing" && !transcript
            ? "Recording completed"
            : status === "processing" && transcript
              ? "Recording completed; transcript available"
              : status === "listening"
                ? "Listening..."
                : status === "speaking"
                  ? "Playing recorded audio..."
                  : status === "error"
                    ? "Something went wrong"
                    : "Voice is ready"}
        </p>
      </div>

      {errorMessage && (
        <p className="mb-4 rounded-lg bg-amber-50 p-3 text-sm text-amber-800">
          {errorMessage}
        </p>
      )}

      <div className="mb-4 rounded-xl bg-gray-50 p-3">
        <p className="mb-2 text-sm font-medium text-gray-700">
          Recognized Text
        </p>

        <p className="whitespace-pre-wrap text-sm text-gray-600">
          {transcript || "Your recognized speech will appear here..."}
        </p>

        {!transcriptionSupported && (
          <p className="mt-2 text-xs text-gray-500">
            Speech-to-text is unavailable in this browser.
          </p>
        )}
      </div>

      {audioUrl && (
        <div className="mb-4">
          <p className="mb-2 text-sm font-medium text-gray-700">
            Recorded Audio
          </p>

          <audio
            src={audioUrl}
            controls
            onPlay={() => setStatus("speaking")}
            onEnded={() => setStatus("idle")}
            className="w-full"
          />
        </div>
      )}
      <div className="mb-4 rounded-xl bg-blue-50 p-4">
  <h3 className="mb-2 font-semibold text-gray-800">
    Text-to-Speech
  </h3>

  <textarea
    value={ttsText}
    onChange={(e) => setTtsText(e.target.value)}
    placeholder="Write text here to hear it..."
    className="mb-3 w-full rounded-lg border border-gray-300 bg-white p-3 text-sm text-gray-900 placeholder:text-gray-500"
    rows={3}
  />

  <div className="flex gap-2">
    <button
      onClick={speakText}
      disabled={isSpeaking}
      className="rounded-lg bg-blue-600 px-4 py-2 text-sm text-white disabled:opacity-50"
    >
      Speak Text
    </button>

    <button
      onClick={stopSpeaking}
      disabled={!isSpeaking}
      className="rounded-lg bg-gray-700 px-4 py-2 text-sm text-white disabled:opacity-50"
    >
      Stop Speaking
    </button>
  </div>
</div>

      <div className="flex flex-wrap gap-2">
        <button
          onClick={startListening}
          disabled={status === "listening"}
          className="rounded-lg bg-blue-600 px-4 py-2 text-sm text-white disabled:opacity-50"
        >
          Start Recording
        </button>

        <button
          onClick={stopListening}
          disabled={status !== "listening"}
          className="rounded-lg bg-gray-700 px-4 py-2 text-sm text-white disabled:opacity-50"
        >
          Stop Recording
        </button>

        <button
          onClick={returnToText}
          className="rounded-lg border border-gray-300 px-4 py-2 text-sm text-gray-700"
        >
          Return to Text Chat
        </button>
      </div>
    </section>
  );
}
