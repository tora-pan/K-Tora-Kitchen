using System;
using System.Collections;
using UnityEngine;

public class CustomerLoop : MonoBehaviour
{
    [SerializeField] private Customer customerPrefab;
    [Tooltip("One is picked at random and added under each spawned customer. Leave empty to use the prefab as is.")]
    [SerializeField] private GameObject[] customerModels = Array.Empty<GameObject>();
    [SerializeField] private RecipeData menuItem;
    [SerializeField] private CashRegister cashRegister;
    [SerializeField] private Transform spawnPoint;
    [SerializeField] private Transform counterPoint;
    [SerializeField] private Transform exitPoint;
    [SerializeField, Min(0f)] private float delayBetweenCustomers = 2f;

    private int lastModelIndex = -1;

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

        if (Array.Exists(customerModels, model => model == null))
        {
            Debug.LogError("CustomerLoop has an empty slot in Customer Models.", this);
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
        AddRandomModel(customer.transform);
        customer.Initialize(menuItem, counterPoint, exitPoint, cashRegister);
        customer.Left += HandleCustomerLeft;
        SetCurrentCustomer(customer);
    }

    private void AddRandomModel(Transform customer)
    {
        if (customerModels.Length == 0)
        {
            return;
        }

        int index = UnityEngine.Random.Range(0, customerModels.Length);
        if (customerModels.Length > 1 && index == lastModelIndex)
        {
            index = (index + 1) % customerModels.Length;
        }

        lastModelIndex = index;
        Instantiate(customerModels[index], customer, false);
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
