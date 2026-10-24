using TMPro;
using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.UI;

public class PrototypeHUD : MonoBehaviour
{
    [SerializeField] private CashRegister cashRegister;
    [SerializeField] private CustomerLoop customerLoop;
    [SerializeField] private SobaSkillCheck skillCheck;
    [SerializeField] private TMP_Text cashText;
    [SerializeField] private TMP_Text orderText;
    [SerializeField] private Button prepareButton;
    [SerializeField] private Button serveButton;

    private Customer trackedCustomer;

    private void Awake()
    {
        if (!HasReferences())
        {
            Debug.LogError("PrototypeHUD is missing Inspector references.", this);
            enabled = false;
        }
    }

    private void OnEnable()
    {
        if (!HasReferences())
        {
            return;
        }

        cashRegister.CashChanged += UpdateCash;
        customerLoop.CustomerChanged += TrackCustomer;
        skillCheck.Started += RefreshOrder;
        skillCheck.Ended += RefreshOrder;
        prepareButton.onClick.AddListener(PrepareCurrentOrder);
        serveButton.onClick.AddListener(customerLoop.ServeCurrentCustomer);

        UpdateCash(cashRegister.Cash);
        TrackCustomer(customerLoop.CurrentCustomer);
    }

    private void OnDisable()
    {
        if (!HasReferences())
        {
            return;
        }

        cashRegister.CashChanged -= UpdateCash;
        customerLoop.CustomerChanged -= TrackCustomer;
        skillCheck.Started -= RefreshOrder;
        skillCheck.Ended -= RefreshOrder;
        prepareButton.onClick.RemoveListener(PrepareCurrentOrder);
        serveButton.onClick.RemoveListener(customerLoop.ServeCurrentCustomer);
        TrackCustomer(null);
    }

    private bool HasReferences()
    {
        return cashRegister != null && customerLoop != null && skillCheck != null
            && cashText != null && orderText != null && prepareButton != null && serveButton != null;
    }

    private void PrepareCurrentOrder()
    {
        // Deselect the button so Space presses during the skill check can't also submit UI.
        if (EventSystem.current != null)
        {
            EventSystem.current.SetSelectedGameObject(null);
        }

        skillCheck.Begin(customerLoop.CurrentCustomer);
    }

    private void RefreshOrder()
    {
        UpdateOrder(trackedCustomer);
    }

    private void UpdateCash(int cash)
    {
        cashText.text = $"Cash: ¥{cash:N0}";
    }

    private void TrackCustomer(Customer customer)
    {
        if (trackedCustomer != null)
        {
            trackedCustomer.StateChanged -= UpdateOrder;
        }

        trackedCustomer = customer;

        if (trackedCustomer != null)
        {
            trackedCustomer.StateChanged += UpdateOrder;
        }

        UpdateOrder(trackedCustomer);
    }

    private void UpdateOrder(Customer customer)
    {
        if (customer == null)
        {
            orderText.text = "Waiting for customer...";
            prepareButton.interactable = false;
            serveButton.interactable = false;
            return;
        }

        switch (customer.CurrentState)
        {
            case Customer.State.WalkingToCounter:
                orderText.text = "Customer approaching...";
                break;
            case Customer.State.Ordering:
                orderText.text = "Customer is ordering...";
                break;
            case Customer.State.WaitingForFood:
                orderText.text = customer.IsOrderPrepared
                    ? $"{customer.Order.DisplayName} is ready - serve it!"
                    : $"Order: {customer.Order.DisplayName} (¥{customer.Order.Price:N0})";
                break;
            case Customer.State.Paying:
            case Customer.State.Leaving:
                orderText.text = customer.LeftUnserved
                    ? "Customer lost patience and left!"
                    : $"Served {customer.Order.DisplayName}!";
                break;
        }

        bool waiting = customer.CurrentState == Customer.State.WaitingForFood;
        prepareButton.interactable = waiting && !customer.IsOrderPrepared && !skillCheck.IsActive;
        serveButton.interactable = waiting && customer.IsOrderPrepared;
    }
}
