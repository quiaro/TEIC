import React, { useEffect, useRef } from 'react';

function Modal({ isOpen, onClose, teamMember, presents }) {
  const modalRef = useRef(null);

  useEffect(() => {
    // Handle escape key press
    const handleEscapeKey = (e) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };

    // Handle click outside modal
    const handleClickOutside = (e) => {
      if (modalRef.current && !modalRef.current.contains(e.target)) {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener('keydown', handleEscapeKey);
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('keydown', handleEscapeKey);
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div className="modal-overlay">
      <div className="modal-container" ref={modalRef}>
        <button className="close-button" onClick={onClose}>
          ×
        </button>
        <div className="modal-header">
          <h2>Ideas de regalo que podrían gustarle a {teamMember}</h2>
        </div>
        <div className="modal-content">
          {presents.map((gift, index) => (
            <div key={index} className="gift-modal-item">
              <h3>{gift.name}</h3>
              <p>
                <em>{gift.description}</em>
              </p>
            </div>
          ))}
        </div>
      </div>

      <style jsx>{`
        .modal-overlay {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background-color: rgba(0, 0, 0, 0.7);
          display: flex;
          justify-content: center;
          align-items: center;
          z-index: 1000;
          animation: fadeIn 0.3s ease-out;
        }

        .modal-container {
          background: rgba(255, 255, 255, 0.95) url('/celebration-bg.jpg')
            no-repeat;
          background-size: cover;
          background-position: center;
          background-blend-mode: overlay;
          border-radius: 8px;
          width: 90%;
          max-width: 600px;
          max-height: 90vh;
          padding: 24px;
          position: relative;
          overflow-y: auto;
          box-shadow: 0 10px 25px rgba(0, 0, 0, 0.3);
        }

        .close-button {
          position: absolute;
          top: 10px;
          right: 10px;
          background: rgba(255, 255, 255, 0.8);
          border: none;
          border-radius: 50%;
          width: 30px;
          height: 30px;
          font-size: 20px;
          cursor: pointer;
          color: #333;
          z-index: 2;
          display: flex;
          align-items: center;
          justify-content: center;
          transition: background-color 0.2s ease;
        }

        .close-button:hover {
          background: rgba(255, 255, 255, 1);
        }

        .modal-header {
          margin-bottom: 20px;
          padding-bottom: 10px;
          border-bottom: 1px solid rgba(234, 234, 234, 0.5);
        }

        .modal-header h2 {
          font-size: 24px;
          color: #333;
          text-align: center;
          text-shadow: 0 1px 2px rgba(255, 255, 255, 0.8);
        }

        .modal-content {
          display: flex;
          flex-direction: column;
          gap: 16px;
        }

        .gift-modal-item {
          background: rgba(255, 255, 255, 0.85);
          padding: 15px;
          border-radius: 6px;
          box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
        }

        .gift-modal-item h3 {
          font-size: 22px;
          margin-bottom: 5px;
          color: #333;
        }

        .gift-modal-item p {
          font-size: 16px;
          color: #555;
          margin: 0;
        }

        @keyframes fadeIn {
          from {
            opacity: 0;
          }
          to {
            opacity: 1;
          }
        }

        @keyframes fadeOut {
          from {
            opacity: 1;
          }
          to {
            opacity: 0;
          }
        }
      `}</style>
    </div>
  );
}

export default Modal;
