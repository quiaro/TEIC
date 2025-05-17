import React, { useState, useRef, useEffect } from 'react';
import Controls from './Controls';
import Header from './Header';
import Modal from './Modal';

function App() {
  const [presents, setPresents] = useState([]);
  const [loading, setLoading] = useState(false);
  const abortControllerRef = useRef(null);

  const [teamMembers, setTeamMembers] = useState([]);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedTeamMember, setSelectedTeamMember] = useState(null);

  useEffect(() => {
    const fetchTeamMembers = async () => {
      try {
        const response = await fetch('/api/teamMembers');
        if (!response.ok) {
          throw new Error(`Error: ${response.status}`);
        }
        const data = await response.json();
        setTeamMembers(data.teamMembers);
      } catch (error) {
        console.error('Failed to fetch teamMembers:', error);
      }
    };

    fetchTeamMembers();
  }, []);

  // Cleanup function for in-progress requests
  useEffect(() => {
    return () => {
      // Abort any in-progress fetch when component unmounts
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);

  const fetchPresents = async (teamMember) => {
    setLoading(true);
    setPresents('');
    setSelectedTeamMember(teamMember);

    // Abort any previous request
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    // Create an AbortController to handle cleanup
    const controller = new AbortController();
    const signal = controller.signal;
    abortControllerRef.current = controller;

    try {
      const response = await fetch(
        `/api/gift-ideas/${encodeURIComponent(teamMember)}`,
        {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
            Accept: 'application/json',
          },
          signal, // Add the abort signal
        }
      );

      if (!response.ok) {
        throw new Error(`Error: ${response.status}`);
      }

      const data = await response.json();
      setPresents(data.giftIdeas);

      // Open the modal when presents are fetched
      setIsModalOpen(true);
    } catch (error) {
      console.error('Error fetching presents:', error);
      setPresents('Error fetching presents. Please try again.');
    } finally {
      if (!signal.aborted) {
        setLoading(false);
        // Clear the abortControllerRef if this request is complete and not aborted
        if (abortControllerRef.current === controller) {
          abortControllerRef.current = null;
        }
      }
    }
  };

  const closeModal = () => {
    // Add quick fade-out animation by adding a class
    const modalOverlay = document.querySelector('.modal-overlay');
    if (modalOverlay) {
      modalOverlay.style.animation = 'fadeOut 0.2s ease-out forwards';
      setTimeout(() => {
        setIsModalOpen(false);
      }, 200);
    } else {
      setIsModalOpen(false);
    }
  };

  return (
    <div className="container">
      <Header />
      {teamMembers.length > 0 && (
        <div className="main-content">
          <div className="controls-wrapper">
            <Controls
              teamMembers={teamMembers}
              onSubmit={fetchPresents}
              loading={loading}
            />
          </div>
        </div>
      )}

      {isModalOpen && presents.length > 0 && (
        <Modal
          isOpen={isModalOpen}
          onClose={closeModal}
          teamMember={selectedTeamMember}
          presents={presents}
        />
      )}

      <style jsx>{`
        .container {
          height: 100vh;
          display: flex;
          flex-direction: column;
          overflow: hidden;
        }
        .main-content {
          display: flex;
          flex: 1;
          gap: 24px;
          padding: 24px;
          min-height: 0; /* This is crucial for nested flex containers to scroll */
          overflow: hidden; /* Prevent content from spilling out */
          width: 100%;
        }
        .controls-wrapper {
          width: 100%;
          min-width: 300px;
          overflow-y: auto; /* Make controls scrollable */
        }
        .content-wrapper {
          flex: 1;
          overflow-y: auto; /* Make content scrollable */
        }

        /* Custom scrollbar styling */
        .controls-wrapper::-webkit-scrollbar,
        .content-wrapper::-webkit-scrollbar {
          width: 8px;
        }

        .controls-wrapper::-webkit-scrollbar-track,
        .content-wrapper::-webkit-scrollbar-track {
          background: #f1f1f1;
          border-radius: 4px;
        }

        .controls-wrapper::-webkit-scrollbar-thumb,
        .content-wrapper::-webkit-scrollbar-thumb {
          background: #c1c1c1;
          border-radius: 4px;
          transition: background 0.2s ease;
        }

        .controls-wrapper::-webkit-scrollbar-thumb:hover,
        .content-wrapper::-webkit-scrollbar-thumb:hover {
          background: #a1a1a1;
        }

        /* Firefox scrollbar styling */
        .controls-wrapper,
        .content-wrapper {
          scrollbar-width: thin;
          scrollbar-color: #c1c1c1 #f1f1f1;
        }
      `}</style>
    </div>
  );
}

export default App;
