import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Fingerprint, AlertCircle, CheckCircle } from 'lucide-react';
import toast from 'react-hot-toast';
import client from '../../api/client';

const FingerprintEnroll = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [scanning, setScanning] = useState(false);
  const [hasTouchId, setHasTouchId] = useState(null); // null=checking, true/false
  const [enrolled, setEnrolled] = useState(false);

  // Check device fingerprint capability
  useEffect(() => {
    if (window.PublicKeyCredential?.isUserVerifyingPlatformAuthenticatorAvailable) {
      window.PublicKeyCredential.isUserVerifyingPlatformAuthenticatorAvailable()
        .then(available => setHasTouchId(available))
        .catch(() => setHasTouchId(false));
    } else {
      setHasTouchId(false);
    }
  }, []);

  const startScan = async () => {
    setScanning(true);
    try {
      const challenge = new Uint8Array(32);
      window.crypto.getRandomValues(challenge);
      const userId = new Uint8Array(16);
      window.crypto.getRandomValues(userId);

      // Use residentKey: "discouraged" to prevent Chrome's "save passkey" dialog
      // authenticatorAttachment: "platform" forces Touch ID / Windows Hello only
      const credential = await navigator.credentials.create({
        publicKey: {
          challenge,
          rp: { id: 'localhost', name: 'Multi-Modal Attendance System' },
          user: { id: userId, name: `student_${id}`, displayName: `Student ${id}` },
          pubKeyCredParams: [{ type: 'public-key', alg: -7 }],
          authenticatorSelection: {
            authenticatorAttachment: 'platform',   // Forces Touch ID — no USB keys / password managers
            userVerification: 'required',
            residentKey: 'discouraged',            // Prevents "Choose where to save passkey" dialog
          },
          timeout: 60000,
          excludeCredentials: [],
        }
      });

      const credentialId = btoa(String.fromCharCode(...new Uint8Array(credential.rawId)));
      await client.post(`/enrollment/fingerprint/${id}`, { credential_id: credentialId });

      toast.success('Fingerprint enrolled successfully!');
      setEnrolled(true);
      setTimeout(() => navigate(`/students/${id}`), 1500);
    } catch (err) {
      console.error(err);
      if (err.name === 'NotAllowedError') {
        toast.error('Touch ID was cancelled or denied. Please try again.');
      } else {
        toast.error('Fingerprint enrollment failed. Please try again.');
      }
    } finally {
      setScanning(false);
    }
  };

  return (
    <div className="max-w-xl mx-auto bg-white p-8 rounded-2xl shadow-sm border border-slate-100 text-center">
      <h1 className="text-2xl font-bold mb-1">Fingerprint Enrollment</h1>
      <p className="text-slate-400 text-sm mb-8">Student Record ID: {id}</p>

      <div className={`flex flex-col items-center justify-center p-12 border-2 border-dashed rounded-2xl mb-8 transition-all ${
        enrolled ? 'border-green-400 bg-green-50' :
        scanning ? 'border-indigo-400 bg-indigo-50' :
        hasTouchId === false ? 'border-slate-200 bg-slate-50' :
        'border-slate-300 bg-slate-50'
      }`}>
        {enrolled ? (
          <CheckCircle className="w-16 h-16 text-green-500 mb-3" />
        ) : (
          <Fingerprint className={`w-16 h-16 mb-3 transition-all ${
            scanning ? 'text-indigo-500 animate-pulse' :
            hasTouchId === false ? 'text-slate-300' : 'text-slate-400'
          }`} />
        )}

        {/* Status text */}
        {hasTouchId === null && <p className="text-slate-500 font-medium">Checking system fingerprint reader...</p>}
        
        {hasTouchId === false && (
          <div className="flex flex-col items-center gap-2">
            <p className="font-bold text-slate-600">No Fingerprint Reader Found</p>
            <p className="text-slate-500 text-sm max-w-xs">
              This system does not have a fingerprint sensor (Touch ID / Windows Hello). 
              Fingerprint enrollment is not available on this device.
            </p>
            <div className="mt-3 flex items-center gap-2 bg-amber-50 border border-amber-200 text-amber-800 px-4 py-2 rounded-xl text-sm font-medium">
              <AlertCircle className="w-4 h-4 shrink-0" />
              Fingerprint not available
            </div>
          </div>
        )}

        {hasTouchId === true && !scanning && !enrolled && (
          <p className="text-slate-600 font-medium">Click "Start Scan" and use Touch ID when prompted.</p>
        )}

        {scanning && (
          <p className="text-indigo-600 font-bold">Waiting for fingerprint... Place your finger on the sensor.</p>
        )}

        {enrolled && (
          <p className="text-green-700 font-bold">Fingerprint enrolled successfully!</p>
        )}
      </div>

      <div className="flex gap-4 justify-center">
        <button onClick={() => navigate(-1)} className="px-6 py-2.5 bg-slate-100 text-slate-700 rounded-xl font-medium hover:bg-slate-200 transition">
          Cancel
        </button>
        {hasTouchId === true && !enrolled && (
          <button onClick={startScan} disabled={scanning}
            className="flex items-center gap-2 px-8 py-2.5 bg-indigo-600 text-white rounded-xl font-bold hover:bg-indigo-700 disabled:opacity-50 transition shadow">
            <Fingerprint className="w-5 h-5" />
            {scanning ? 'Scanning...' : 'Start Scan'}
          </button>
        )}
        {hasTouchId === false && (
          <button onClick={() => navigate(-1)} className="px-6 py-2.5 bg-slate-700 text-white rounded-xl font-medium hover:bg-slate-800 transition">
            Go Back
          </button>
        )}
      </div>
    </div>
  );
};

export default FingerprintEnroll;
