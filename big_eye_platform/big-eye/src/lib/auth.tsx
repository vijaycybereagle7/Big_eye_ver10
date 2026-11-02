import React, { useEffect, useState } from 'react';
import { isSupabaseConfigured, supabase } from './supabase';
import { AuthContext, User } from './auth-context';

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check for existing session
    async function loadUser() {
      setLoading(true);
      if (!isSupabaseConfigured) {
        setLoading(false);
        return;
      }

      try {
        const { data: { user } } = await supabase.auth.getUser();
        setUser(user);
      } catch (error) {
        // Preview mode must remain usable if Auth is not configured or is
        // temporarily unavailable.
        console.warn('Supabase session could not be restored:', error);
      } finally {
        setLoading(false);
      }
    }
    
    loadUser();

    if (!isSupabaseConfigured) return;

    // Keep auth listener synchronous. Profile sync is handled outside the
    // listener to avoid blocking Supabase Auth callbacks.
    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      setUser(session?.user || null);
    });

    return () => subscription.unsubscribe();
  }, []);

  const signInWithEmail = async (email: string, password: string) => {
    const { error } = await supabase.auth.signInWithPassword({
      email,
      password,
    });
    
    if (error) {
      console.error('Email sign-in error:', error);
      throw error;
    }

    // Update profile with device info after successful login
    await updateUserProfile({});
  };

  const signUpWithEmail = async (email: string, password: string) => {
    const { error } = await supabase.auth.signUp({
      email,
      password,
      options: {
        emailRedirectTo: `${window.location.origin}/`,
        data: {
          email_confirmed: false
        }
      }
    });
    
    if (error) {
      console.error('Email sign-up error:', error);
      throw error;
    }
  };

  const signInWithGoogle = async () => {
    const { error } = await supabase.auth.signInWithOAuth({
      provider: 'google',
      options: {
        redirectTo: `${window.location.origin}/`,
      },
    });
    
    if (error) {
      console.error('Google sign-in error:', error);
      throw error;
    }
  };

  const updateUserProfile = async (profileData: any) => {
    if (!isSupabaseConfigured || typeof navigator === 'undefined') return;

    try {
      // Get device and location information
      const deviceInfo = {
        userAgent: navigator.userAgent,
        platform: navigator.platform,
        language: navigator.language,
        ...profileData
      };

      // Parse browser and OS
      const ua = navigator.userAgent;
      let browser = 'Unknown';
      let os = 'Unknown';

      if (ua.includes('Chrome')) browser = 'Chrome';
      else if (ua.includes('Firefox')) browser = 'Firefox';
      else if (ua.includes('Safari')) browser = 'Safari';
      else if (ua.includes('Edge')) browser = 'Edge';

      if (ua.includes('Windows')) os = 'Windows';
      else if (ua.includes('Mac')) os = 'macOS';
      else if (ua.includes('Linux')) os = 'Linux';
      else if (ua.includes('Android')) os = 'Android';
      else if (ua.includes('iOS')) os = 'iOS';

      // Get IP and location from external API (free service)
      let ipAddress = 'Unknown';
      let location = 'Unknown';

      try {
        const ipResponse = await fetch('https://api.ipify.org?format=json');
        const ipData = await ipResponse.json();
        ipAddress = ipData.ip;

        // Get location from IP
        const geoResponse = await fetch(`https://ipapi.co/${ipAddress}/json/`);
        const geoData = await geoResponse.json();
        location = `${geoData.city || 'Unknown'}, ${geoData.country_name || 'Unknown'}`;
      } catch (error) {
        console.error('Error fetching IP/location:', error);
      }

      // Call edge function to update profile
      await supabase.functions.invoke('update-user-profile', {
        body: {
          ipAddress,
          deviceInfo,
          deviceName: navigator.platform,
          browser,
          os,
          location
        }
      });
    } catch (error) {
      console.error('Error updating user profile:', error);
    }
  };

  const signOut = async () => {
    if (!isSupabaseConfigured) return;
    await supabase.auth.signOut();
  };

  return (
    <AuthContext.Provider value={{ 
      user, 
      loading, 
      signInWithEmail, 
      signUpWithEmail, 
      signInWithGoogle, 
      signOut, 
      updateUserProfile 
    }}>
      {children}
    </AuthContext.Provider>
  );
}
