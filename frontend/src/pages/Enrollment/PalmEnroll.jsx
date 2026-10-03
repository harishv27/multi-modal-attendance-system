import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import SmartWebcamCapture from '../../components/SmartWebcamCapture';
import toast from 'react-hot-toast';
import client from '../../api/client';

const PalmEnroll = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [image, setImage] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async () => {
    if (!image) return toast.error('Please capture an image first');
    setLoading(true);
    try {
      await client.post(`/enrollment/palm/${id}`, { image_base64: image });
      toast.success('Palm enrolled successfully!');
      navigate(`/students/${id}`);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to enroll palm');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-xl mx-auto bg-white p-6 rounded-xl shadow-sm border border-slate-100 text-center">
      <h1 className="text-2xl font-bold mb-2">Palm Enrollment</h1>
      <p className="text-slate-500 mb-6">Student ID: {id}</p>
      
      <SmartWebcamCapture 
        onCapture={setImage} 
        title="Capture Palm"
        instructions="Hold your palm flat and steady in front of the camera."
      />

      <div className="mt-8 flex gap-4 justify-center">
        <button onClick={() => navigate(-1)} className="px-6 py-2 bg-slate-100 text-slate-700 rounded-lg hover:bg-slate-200">Cancel</button>
        <button 
          onClick={handleSubmit} 
          disabled={!image || loading} 
          className="px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50"
        >
          {loading ? 'Processing...' : 'Submit Enrollment'}
        </button>
      </div>
    </div>
  );
};

export default PalmEnroll;
