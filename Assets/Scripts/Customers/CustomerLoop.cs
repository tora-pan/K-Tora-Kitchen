using System;
using System.Collections;
using UnityEngine;

public class CustomerLoop : MonoBehaviour
{
    [SerializeField] private Customer customerPrefab;
    [SerializeField] private RecipeData menuItem;
    [SerializeField] private CashRegister cashRegister;
    [SerializeField] private Transform spawnPoint;
    [SerializeField] private Transform counterPoint;
    [SerializeField] private Transform exitPoint;
    [SerializeField, Min(0f)] private float delayBetweenCustomers = 2f;

    public Customer CurrentCustomer { get; private set; }

    public event Action<Customer> CustomerChanged;

    private void Start()
    {
        if (customerPrefab == null || menuItem == null || cashRegister == null
            || spawnPoint == null || counterPoint == null || exitPoint == null)
        {
            Debug.LogError("CustomerLoop is missing Inspector references.", this);
            enabled = false;
            return;
        }

        SpawnCustomer();
    }

    public void ServeCurrentCustomer()
    {
        if (CurrentCustomer != null)
        {
            CurrentCustomer.TryServe();
        }
    }

    private void SpawnCustomer()
    {
        Customer customer = Instantiate(customerPrefab, spawnPoint.position, spawnPoint.rotation);
        customer.Initialize(menuItem, counterPoint, exitPoint, cashRegister);
        customer.Left += HandleCustomerLeft;
        SetCurrentCustomer(customer);
    }

    private void HandleCustomerLeft(Customer customer)
    {
        customer.Left -= HandleCustomerLeft;
        SetCurrentCustomer(null);
        StartCoroutine(SpawnAfterDelay());
    }

    private IEnumerator SpawnAfterDelay()
    {
        yield return new WaitForSeconds(delayBetweenCustomers);
        SpawnCustomer();
    }

    private void SetCurrentCustomer(Customer customer)
    {
        CurrentCustomer = customer;
        CustomerChanged?.Invoke(customer);
    }
}
