using TMPro;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.InputSystem.UI;
using UnityEngine.UI;

// One-shot helper that builds the remaining prototype objects in the open scene.
// Existing objects/assets with the same names are reused, so it is safe to run again.
public static class PrototypeSetupBuilder
{
    private const string RecipePath = "Assets/ScriptableObjects/Recipes/Soba.asset";
    private const string CustomerMaterialPath = "Assets/Materials/Customer.mat";
    private const string CustomerPrefabPath = "Assets/Prefabs/Customer.prefab";
    private const float CustomerHeight = 1.2f;
    private const float CounterStandOff = 0.7f;
    private const float PathHalfWidth = 9f;

    [MenuItem("K-Tora/Build Prototype Setup")]
    private static void Build()
    {
        if (Resources.Load<TMP_Settings>("TMP Settings") == null)
        {
            EditorUtility.DisplayDialog("TMP Essentials missing",
                "Import them first via Window > TextMeshPro > Import TMP Essential Resources, then run this again.", "OK");
            return;
        }

        GameObject counter = GameObject.Find("FoodTruck/TruckCounter");
        if (counter == null || !counter.TryGetComponent(out Renderer counterRenderer))
        {
            EditorUtility.DisplayDialog("Counter not found",
                "Open the scene containing FoodTruck/TruckCounter (with a MeshRenderer) and run this again.", "OK");
            return;
        }

        Bounds counterBounds = counterRenderer.bounds;
        var counterPointPosition = new Vector3(counterBounds.center.x, 0f, counterBounds.min.z - CounterStandOff);

        Transform counterPoint = FindOrCreatePoint("CounterPoint", counter.transform.parent, counterPointPosition);
        Transform path = FindOrCreateRoot("CustomerPath").transform;
        Transform spawnPoint = FindOrCreatePoint("SpawnPoint", path, counterPointPosition + Vector3.left * PathHalfWidth);
        Transform exitPoint = FindOrCreatePoint("ExitPoint", path, counterPointPosition + Vector3.right * PathHalfWidth);

        RecipeData soba = LoadOrCreateRecipe();
        Customer customerPrefab = LoadOrCreateCustomerPrefab();

        GameObject gameLoop = FindOrCreateRoot("GameLoop");
        CashRegister cashRegister = GetOrAdd<CashRegister>(gameLoop);
        CustomerLoop customerLoop = GetOrAdd<CustomerLoop>(gameLoop);
        PrototypeHUD hud = GetOrAdd<PrototypeHUD>(gameLoop);

        AssignReferences(customerLoop,
            ("customerPrefab", customerPrefab),
            ("menuItem", soba),
            ("cashRegister", cashRegister),
            ("spawnPoint", spawnPoint),
            ("counterPoint", counterPoint),
            ("exitPoint", exitPoint));

        BuildHud(out TMP_Text cashText, out TMP_Text orderText, out Button serveButton);
        AssignReferences(hud,
            ("cashRegister", cashRegister),
            ("customerLoop", customerLoop),
            ("cashText", cashText),
            ("orderText", orderText),
            ("serveButton", serveButton));

        EnsureEventSystem();

        EditorSceneManager.MarkSceneDirty(gameLoop.scene);
        Selection.activeGameObject = gameLoop;
        Debug.Log("Prototype setup complete. Save the scene, then press Play.");
    }

    private static GameObject FindOrCreateRoot(string name)
    {
        GameObject existing = GameObject.Find(name);
        if (existing != null)
        {
            return existing;
        }

        var created = new GameObject(name);
        Undo.RegisterCreatedObjectUndo(created, $"Create {name}");
        return created;
    }

    private static Transform FindOrCreatePoint(string name, Transform parent, Vector3 worldPosition)
    {
        Transform existing = parent != null ? parent.Find(name) : null;
        if (existing != null)
        {
            return existing;
        }

        var point = new GameObject(name);
        Undo.RegisterCreatedObjectUndo(point, $"Create {name}");
        point.transform.SetParent(parent, false);
        point.transform.position = worldPosition;
        return point.transform;
    }

    private static T GetOrAdd<T>(GameObject target) where T : Component
    {
        return target.TryGetComponent(out T component) ? component : Undo.AddComponent<T>(target);
    }

    private static void AssignReferences(Object target, params (string field, Object value)[] references)
    {
        var serialized = new SerializedObject(target);
        foreach ((string field, Object value) in references)
        {
            SerializedProperty property = serialized.FindProperty(field);
            if (property == null)
            {
                Debug.LogError($"Field '{field}' not found on {target.GetType().Name}.", target);
                continue;
            }

            property.objectReferenceValue = value;
        }

        serialized.ApplyModifiedProperties();
    }

    private static RecipeData LoadOrCreateRecipe()
    {
        var recipe = AssetDatabase.LoadAssetAtPath<RecipeData>(RecipePath);
        if (recipe != null)
        {
            return recipe;
        }

        EnsureFolder("Assets/ScriptableObjects/Recipes");
        recipe = ScriptableObject.CreateInstance<RecipeData>();
        AssetDatabase.CreateAsset(recipe, RecipePath);
        return recipe;
    }

    private static Customer LoadOrCreateCustomerPrefab()
    {
        var existing = AssetDatabase.LoadAssetAtPath<Customer>(CustomerPrefabPath);
        if (existing != null)
        {
            return existing;
        }

        var root = new GameObject("Customer");
        root.AddComponent<Customer>();

        GameObject body = GameObject.CreatePrimitive(PrimitiveType.Capsule);
        body.name = "Body";
        body.transform.SetParent(root.transform, false);
        body.transform.localPosition = new Vector3(0f, CustomerHeight * 0.5f, 0f);
        body.transform.localScale = new Vector3(0.4f, CustomerHeight * 0.5f, 0.4f);
        Object.DestroyImmediate(body.GetComponent<Collider>());
        body.GetComponent<MeshRenderer>().sharedMaterial = LoadOrCreateCustomerMaterial();

        EnsureFolder("Assets/Prefabs");
        GameObject prefab = PrefabUtility.SaveAsPrefabAsset(root, CustomerPrefabPath);
        Object.DestroyImmediate(root);
        return prefab.GetComponent<Customer>();
    }

    private static Material LoadOrCreateCustomerMaterial()
    {
        var material = AssetDatabase.LoadAssetAtPath<Material>(CustomerMaterialPath);
        if (material != null)
        {
            return material;
        }

        Shader shader = Shader.Find("Universal Render Pipeline/Lit");
        material = new Material(shader);
        material.SetColor("_BaseColor", new Color(0.25f, 0.5f, 0.9f));
        EnsureFolder("Assets/Materials");
        AssetDatabase.CreateAsset(material, CustomerMaterialPath);
        return material;
    }

    private static void BuildHud(out TMP_Text cashText, out TMP_Text orderText, out Button serveButton)
    {
        GameObject canvasObject = GameObject.Find("HUD");
        if (canvasObject == null)
        {
            canvasObject = new GameObject("HUD", typeof(Canvas), typeof(CanvasScaler), typeof(GraphicRaycaster));
            Undo.RegisterCreatedObjectUndo(canvasObject, "Create HUD");
            canvasObject.GetComponent<Canvas>().renderMode = RenderMode.ScreenSpaceOverlay;
            var scaler = canvasObject.GetComponent<CanvasScaler>();
            scaler.uiScaleMode = CanvasScaler.ScaleMode.ScaleWithScreenSize;
            scaler.referenceResolution = new Vector2(1920f, 1080f);
        }

        Transform canvas = canvasObject.transform;
        var resources = new TMP_DefaultControls.Resources();

        cashText = FindOrCreateText(canvas, "CashText", resources, new Vector2(40f, -40f));
        orderText = FindOrCreateText(canvas, "OrderText", resources, new Vector2(40f, -100f));

        Transform existingButton = canvas.Find("ServeButton");
        if (existingButton != null)
        {
            serveButton = existingButton.GetComponent<Button>();
            return;
        }

        GameObject buttonObject = TMP_DefaultControls.CreateButton(resources);
        buttonObject.name = "ServeButton";
        buttonObject.transform.SetParent(canvas, false);
        var rect = (RectTransform)buttonObject.transform;
        rect.anchorMin = rect.anchorMax = rect.pivot = new Vector2(0.5f, 0f);
        rect.anchoredPosition = new Vector2(0f, 60f);
        rect.sizeDelta = new Vector2(320f, 80f);
        var label = buttonObject.GetComponentInChildren<TMP_Text>();
        label.text = "Serve Soba";
        label.fontSize = 36f;
        serveButton = buttonObject.GetComponent<Button>();
    }

    private static TMP_Text FindOrCreateText(Transform canvas, string name, TMP_DefaultControls.Resources resources, Vector2 topLeftOffset)
    {
        Transform existing = canvas.Find(name);
        if (existing != null)
        {
            return existing.GetComponent<TMP_Text>();
        }

        GameObject textObject = TMP_DefaultControls.CreateText(resources);
        textObject.name = name;
        textObject.transform.SetParent(canvas, false);
        var rect = (RectTransform)textObject.transform;
        rect.anchorMin = rect.anchorMax = rect.pivot = new Vector2(0f, 1f);
        rect.anchoredPosition = topLeftOffset;
        rect.sizeDelta = new Vector2(800f, 60f);
        var text = textObject.GetComponent<TMP_Text>();
        text.fontSize = 40f;
        text.color = Color.white;
        text.text = name;
        return text;
    }

    private static void EnsureEventSystem()
    {
        if (Object.FindFirstObjectByType<EventSystem>() != null)
        {
            return;
        }

        var eventSystem = new GameObject("EventSystem", typeof(EventSystem), typeof(InputSystemUIInputModule));
        Undo.RegisterCreatedObjectUndo(eventSystem, "Create EventSystem");
    }

    private static void EnsureFolder(string path)
    {
        if (AssetDatabase.IsValidFolder(path))
        {
            return;
        }

        string parent = System.IO.Path.GetDirectoryName(path).Replace('\\', '/');
        EnsureFolder(parent);
        AssetDatabase.CreateFolder(parent, System.IO.Path.GetFileName(path));
    }
}
