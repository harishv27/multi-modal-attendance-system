import { useState } from 'react';
import toast from 'react-hot-toast';
import { Camera, Hand, Fingerprint, CheckCircle, XCircle, ChevronRight } from 'lucide-react';
import client from '../../api/client';
import SmartWebcamCapture from '../../components/SmartWebcamCapture';

const MarkAttendance = () => {
  const [step, setStep] = useState(1);
  const [faceImg, setFaceImg] = useState(null);
  const [palmImg, setPalmImg] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  const handleCaptureFace = (img) => {
    if (img) setFaceImg(img);
    // Don't auto-advance — user clicks "Continue" button
  };

  const handleCapturePalm = (img) => {
    if (img) setPalmImg(img);
    // Don't auto-advance — user clicks "Continue" button
  };

  const handleScanFingerprint = async () => {
    if (!window.PublicKeyCredential) {
      toast('No biometric hardware detected. Proceeding without fingerprint.', { icon: '⚠️' });
      await verifyAll(null);
      return;
    }

    try {
      setLoading(true);
      const challenge = new Uint8Array(32);
      window.crypto.getRandomValues(challenge);

      const assertion = await navigator.credentials.get({
        publicKey: {
          challenge,
          userVerification: 'required',
          timeout: 30000,
        }
      });

      const credId = btoa(String.fromCharCode(...new Uint8Array(assertion.rawId)));
      await verifyAll(credId);
    } catch (err) {
      if (err.name === 'NotAllowedError') {
        toast.error('Fingerprint scan cancelled or not allowed.');
      } else {
        toast('Could not scan fingerprint. Using Face/Palm only.', { icon: '⚠️' });
        await verifyAll(null);
      }
    } finally {
      setLoading(false);
    }
  };

  const verifyAll = async (fingerprintCredId) => {
    setLoading(true);
    try {
      const res = await client.post('/attendance/verify/multimodal', {
        face_image: faceImg,
        palm_image: palmImg,
        fingerprint_credential_id: fingerprintCredId || null,
      });

      setResult(res.data);
      if (res.data.match) {
        toast.success(`✅ Attendance marked for ${res.data.student_name}!`);
      } else {
        toast.error('❌ Verification failed. Identity not confirmed.');
      }
      setStep(4);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Verification error. Please try again.');
      reset();
    } finally {
      setLoading(false);
    }
  };

  const reset = () => {
    setStep(1);
    setFaceImg(null);
    setPalmImg(null);
    setResult(null);
  };

  const stepLabels = ['Face', 'Palm', 'Fingerprint'];

  return (
    <div className="space-y-6 max-w-2xl mx-auto">
      <h1 className="text-2xl font-bold text-slate-800 text-center">Mark Attendance</h1>

      {/* Step indicator */}
      {step <= 3 && (
        <div className="flex justify-center items-center gap-3 mb-6">
          {[1, 2, 3].map(s => (
            <div key={s} className="flex items-center gap-3">
              <div className={`flex flex-col items-center`}>
                <div className={`flex items-center justify-center w-10 h-10 rounded-full font-bold text-sm transition-all ${
                  step > s ? 'bg-green-500 text-white' :
                  step === s ? 'bg-indigo-600 text-white ring-4 ring-indigo-100' :
                  'bg-slate-200 text-slate-500'
                }`}>
                  {step > s ? '✓' : s}
                </div>
                <span className={`text-xs mt-1 font-medium ${step === s ? 'text-indigo-600' : 'text-slate-400'}`}>
                  {stepLabels[s - 1]}
                </span>
              </div>
              {s < 3 && <div className={`w-14 h-1 rounded ${step > s ? 'bg-green-500' : 'bg-slate-200'} mb-3`} />}
            </div>
          ))}
        </div>
      )}

      <div className="bg-white rounded-2xl shadow-lg border border-slate-100 p-8">

        {/* Step 1: Face */}
        {step === 1 && (
          <div className="space-y-5 flex flex-col items-center">
            <div className="text-center">
              <Camera className="w-10 h-10 text-indigo-500 mx-auto mb-2" />
              <h2 className="text-xl font-bold text-slate-800">Step 1: Face Recognition</h2>
              <p className="text-slate-500 text-sm mt-1">Look directly at the camera until the green box appears.</p>
            </div>
            <SmartWebcamCapture title="" mode="face" onCapture={handleCaptureFace} />
            {faceImg && (
              <button
                onClick={() => setStep(2)}
                className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white font-bold px-8 py-3 rounded-xl shadow-lg transition"
              >
                Continue to Palm <ChevronRight className="w-5 h-5" />
              </button>
            )}
          </div>
        )}

        {/* Step 2: Palm */}
        {step === 2 && (
          <div className="space-y-5 flex flex-col items-center">
            <div className="text-center">
              <Hand className="w-10 h-10 text-indigo-500 mx-auto mb-2" />
              <h2 className="text-xl font-bold text-slate-800">Step 2: Palm Print</h2>
              <p className="text-slate-500 text-sm mt-1">Hold your palm flat, facing the camera, until the blue box appears.</p>
            </div>
            <SmartWebcamCapture title="" mode="palm" onCapture={handleCapturePalm} />
            <div className="flex gap-3">
              {palmImg && (
                <button
                  onClick={() => setStep(3)}
                  className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white font-bold px-8 py-3 rounded-xl shadow-lg transition"
                >
                  Continue to Fingerprint <ChevronRight className="w-5 h-5" />
                </button>
              )}
              <button
                onClick={() => setStep(3)}
                className="text-slate-500 underline text-sm px-4 py-3"
              >
                Skip Palm
              </button>
            </div>
          </div>
        )}

        {/* Step 3: Fingerprint */}
        {step === 3 && (
          <div className="flex flex-col items-center space-y-6 text-center py-6">
            <Fingerprint className="w-20 h-20 text-indigo-500" />
            <h2 className="text-2xl font-bold text-slate-800">Step 3: Fingerprint</h2>
            <p className="text-slate-500 max-w-sm">
              Click the button below to use your Mac's Touch ID / Windows Hello to verify your identity.
            </p>
            <button
              onClick={handleScanFingerprint}
              disabled={loading}
              className="flex items-center gap-3 px-10 py-4 bg-indigo-600 text-white text-lg font-bold rounded-2xl hover:bg-indigo-700 shadow-xl disabled:opacity-50 transition"
            >
              <Fingerprint className="w-6 h-6" />
              {loading ? 'Verifying...' : 'Scan & Verify Fingerprint'}
            </button>
            <button
              onClick={() => verifyAll(null)}
              disabled={loading}
              className="text-slate-400 underline text-sm"
            >
              Skip Fingerprint (Use Face/Palm Only)
            </button>
          </div>
        )}

        {/* Step 4: Result */}
        {step === 4 && result && (
          <div className="text-center py-4">
            {result.match ? (
              <div className="space-y-4">
                <CheckCircle className="w-20 h-20 text-green-500 mx-auto" />
                <h2 className="text-3xl font-bold text-green-600">VERIFIED</h2>
                <p className="text-xl font-semibold text-slate-700">{result.student_name}</p>

                <div className="max-w-sm mx-auto bg-slate-50 rounded-xl p-5 space-y-3 text-left border border-slate-200">
                  {[
                    { label: 'Face Match', val: result.fusion_result?.individual_scores?.face },
                    { label: 'Palm Match', val: result.fusion_result?.individual_scores?.palm },
                    { label: 'Fingerprint', val: result.fusion_result?.individual_scores?.fingerprint },
                  ].map(({ label, val }) => (
                    <div key={label} className="flex justify-between items-center border-b border-slate-100 pb-2">
                      <span className="text-slate-600 text-sm">{label}</span>
                      <span className="font-bold text-indigo-600 text-sm">
                        {val !== undefined && val !== null
                          ? label === 'Fingerprint' ? 'Valid ✓' : `${(val * 100).toFixed(1)}%`
                          : 'Not used'}
                      </span>
                    </div>
                  ))}
                  <div className="flex justify-between items-center pt-1">
                    <span className="font-bold text-slate-700">Fusion Score</span>
                    <span className="font-black text-green-600 text-lg">
                      {(result.fusion_result?.fusion_score * 100).toFixed(1)}%
                    </span>
                  </div>
                </div>
              </div>
            ) : (
              <div className="space-y-4">
                <XCircle className="w-20 h-20 text-red-500 mx-auto" />
                <h2 className="text-3xl font-bold text-red-600">ACCESS DENIED</h2>
                <p className="text-slate-500">{result.fusion_result?.message || 'Identity could not be confirmed.'}</p>
              </div>
            )}

            <button
              onClick={reset}
              className="mt-8 px-10 py-3 bg-slate-800 text-white font-bold rounded-xl hover:bg-slate-900 shadow-lg transition"
            >
              Mark Another Attendance
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default MarkAttendance;
