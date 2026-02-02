import { useState, useEffect, useRef } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

export default function Login() {
  const [formData, setFormData] = useState({
    username: '',
    password: ''
  });
  const [errors, setErrors] = useState({});
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [rateLimitInfo, setRateLimitInfo] = useState(null);
  const [countdown, setCountdown] = useState(0);
  
  const countdownInterval = useRef(null);
  const navigate = useNavigate();
  const { login } = useAuth();

  // Countdown timer effect
  useEffect(() => {
    if (countdown > 0) {
      countdownInterval.current = setInterval(() => {
        setCountdown(prev => {
          if (prev <= 1) {
            // Countdown finished
            clearInterval(countdownInterval.current);
            setRateLimitInfo(null);
            setErrors({});
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
    }

    return () => {
      if (countdownInterval.current) {
        clearInterval(countdownInterval.current);
      }
    };
  }, [countdown]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    setErrors(prev => ({ ...prev, [name]: '', general: '' }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Clear previous errors
    setErrors({});
    setRateLimitInfo(null);
    setCountdown(0);
    setLoading(true);

    try {
      await login(formData.username, formData.password);
      navigate('/');
    } catch (err) {
      const errorMessage = err.message.toLowerCase();
      
      if (errorMessage.includes('rate limit') || errorMessage.includes('too many')) {
        const retryAfter = 60; // seconds
        setRateLimitInfo({
          message: '⏱️ Too many login attempts',
          detail: 'Please wait before trying again. This protects your account from unauthorized access.',
          retryAfter: retryAfter
        });
        setCountdown(retryAfter);
        setErrors({ general: 'Rate limit exceeded' });
      } else if (errorMessage.includes('incorrect') || errorMessage.includes('invalid')) {
        setErrors({ 
          general: '❌ Invalid username or password',
          detail: 'Please check your credentials and try again.'
        });
      } else if (errorMessage.includes('inactive')) {
        setErrors({ 
          general: '🚫 Account inactive',
          detail: 'Your account has been deactivated. Please contact support.'
        });
      } else {
        setErrors({ general: err.message });
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-600 via-blue-700 to-blue-800 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Logo/Brand */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-white rounded-2xl shadow-lg mb-4">
            <span className="text-3xl">🤖</span>
          </div>
          <h1 className="text-3xl font-bold text-white mb-2">AI DevOps Monitor</h1>
          <p className="text-blue-200">Sign in to your account</p>
        </div>

        {/* Login Card */}
        <div className="bg-white rounded-2xl shadow-2xl p-8">
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Rate Limit Warning */}
            {rateLimitInfo && countdown > 0 && (
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                <div className="flex items-start gap-3">
                  <span className="text-2xl">⏱️</span>
                  <div className="flex-1">
                    <h3 className="font-semibold text-yellow-800 mb-1">{rateLimitInfo.message}</h3>
                    <p className="text-sm text-yellow-700">{rateLimitInfo.detail}</p>
                    <div className="mt-3 flex items-center gap-2">
                      <div className="flex-1 bg-yellow-200 rounded-full h-2 overflow-hidden">
                        <div 
                          className="bg-yellow-600 h-full transition-all duration-1000 ease-linear"
                          style={{ width: `${(countdown / rateLimitInfo.retryAfter) * 100}%` }}
                        />
                      </div>
                      <span className="text-sm font-semibold text-yellow-800 min-w-[3rem] text-right">
                        {countdown}s
                      </span>
                    </div>
                    <p className="text-xs text-yellow-600 mt-2">
                      {countdown > 0 ? 'Form will be available automatically when timer ends' : 'You can try again now!'}
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* General Error */}
            {errors.general && !rateLimitInfo && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                <div className="flex items-start gap-2">
                  <span className="text-red-600 font-semibold">{errors.general}</span>
                </div>
                {errors.detail && (
                  <p className="text-sm text-red-600 mt-1">{errors.detail}</p>
                )}
              </div>
            )}

            {/* Username */}
            <div>
              <label htmlFor="username" className="block text-sm font-semibold text-gray-700 mb-2">
                Username
              </label>
              <input
                id="username"
                name="username"
                type="text"
                value={formData.username}
                onChange={handleChange}
                required
                autoComplete="username"
                className={`w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all ${
                  errors.username ? 'border-red-300 bg-red-50' : 'border-gray-300'
                }`}
                placeholder="Enter your username"
                disabled={loading}
              />
              {errors.username && (
                <p className="mt-1 text-sm text-red-600">{errors.username}</p>
              )}
            </div>

            {/* Password */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <label htmlFor="password" className="block text-sm font-semibold text-gray-700">
                  Password
                </label>
                <Link 
                  to="/forgot-password" 
                  className="text-sm text-blue-600 hover:text-blue-700 hover:underline"
                >
                  Forgot password?
                </Link>
              </div>
              <div className="relative">
                <input
                  id="password"
                  name="password"
                  type={showPassword ? 'text' : 'password'}
                  value={formData.password}
                  onChange={handleChange}
                  required
                  autoComplete="current-password"
                  className={`w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all pr-10 ${
                    errors.password ? 'border-red-300 bg-red-50' : 'border-gray-300'
                  }`}
                  placeholder="Enter your password"
                  disabled={loading}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-700 disabled:opacity-50"
                  disabled={loading}
                  tabIndex={-1}
                >
                  {showPassword ? '🙈' : '👁️'}
                </button>
              </div>
              {errors.password && (
                <p className="mt-1 text-sm text-red-600">{errors.password}</p>
              )}
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={loading || countdown > 0}
              className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 px-4 rounded-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-lg hover:shadow-xl transform hover:-translate-y-0.5"
            >
              {loading ? (
                <span className="flex items-center justify-center gap-2">
                  <span className="animate-spin">⏳</span>
                  Signing in...
                </span>
              ) : countdown > 0 ? (
                <span className="flex items-center justify-center gap-2">
                  ⏱️ Wait {countdown}s
                </span>
              ) : (
                'Sign In'
              )}
            </button>
          </form>

          <div className="mt-6 text-center">
            <p className="text-sm text-gray-600">
              Don't have an account?{' '}
              <Link to="/register" className="text-blue-600 hover:text-blue-700 font-semibold hover:underline">
                Sign up
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
