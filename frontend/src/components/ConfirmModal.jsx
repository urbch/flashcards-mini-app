import './ConfirmModal.css';

const ConfirmModal = ({ isOpen, message, onConfirm, onCancel }) => {
  if (!isOpen) return null;

  return (
    <div className="modal-overlay">
      <div className="confirm-modal">
        <p>{message}</p>
        <div className="modal-buttons">
          <button className="confirm-button" onClick={onConfirm}>
            Подтвердить
          </button>
          <button className="cancel-button" onClick={onCancel}>
            Отменить
          </button>
        </div>
      </div>
    </div>
  );
};

export default ConfirmModal;
