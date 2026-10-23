using TMPro;
using UnityEngine;
using UnityEngine.UI;

public class PrototypeHUD : MonoBehaviour
{
    [SerializeField] private CashRegister cashRegister;
    [SerializeField] private CustomerLoop customerLoop;
    [SerializeField] private TMP_Text cashText;
    [SerializeField] private TMP_Text orderText;
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
        serveButton.onClick.RemoveListener(customerLoop.ServeCurrentCustomer);
        TrackCustomer(null);
    }

    private bool HasReferences()
    {
        return cashRegister != null && customerLoop != null
            && cashText != null && orderText != null && serveButton != null;
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
                orderText.text = $"Order: {customer.Order.DisplayName} (¥{customer.Order.Price:N0})";
                break;
            case Customer.State.Paying:
            case Customer.State.Leaving:
                orderText.text = $"Served {customer.Order.DisplayName}!";
                break;
        }

        serveButton.interactable = customer.CurrentState == Customer.State.WaitingForFood;
    }
}
