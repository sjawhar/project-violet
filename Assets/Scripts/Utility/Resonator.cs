using System.Collections;
using UnityEngine;

namespace Buffalo
{
    public enum ResonateColor
    {
        None,
        Blue,
        Green,
        Red,
        Yellow
    }

    public class Resonator : MonoBehaviour
    {
        [Tooltip("The Layer with which the character should not collide while phasing blue.")]
        public string blueLayerName;
        LayerMask m_BlueLayerMask;
        int m_BlueLayerId;

        [Tooltip("The Layer with which the character should not collide while phasing green.")]
        public string greenLayerName;
        LayerMask m_GreenLayerMask;
        int m_GreenLayerId;

        [Tooltip("The Layer with which the character should not collide while phasing red.")]
        public string redLayerName;
        LayerMask m_RedLayerMask;
        int m_RedLayerId;

        [Tooltip("The Layer with which the character should not collide while phasing yellow.")]
        public string yellowLayerName;
        LayerMask m_YellowLayerMask;
        int m_YellowLayerId;


        ResonateColor m_CurrentColor = ResonateColor.None;
        float m_ResonateTime = 3f;
        float m_TimeRemaining = 0f;
        IEnumerator m_Coroutine;

        static Resonator s_Instance;
        static Resonator Instance
        {
            get
            {
                if (s_Instance != null)
                {
                    return s_Instance;
                }

                s_Instance = FindObjectOfType<Resonator>();

                if (s_Instance != null)
                {
                    return s_Instance;
                }

                Create();

                return s_Instance;
            }
            set { s_Instance = value; }
        }

        static void Create()
        {
            GameObject resonatorGameObject = new GameObject("Resonator");
            s_Instance = resonatorGameObject.AddComponent<Resonator> ();
        }

        void Awake()
        {
            if (Instance != this)
            {
                Destroy(gameObject);
                return;
            }

            m_BlueLayerMask = LayerMask.GetMask(blueLayerName);
            m_BlueLayerId = LayerMask.NameToLayer(blueLayerName);

            m_GreenLayerMask = LayerMask.GetMask(greenLayerName);
            m_GreenLayerId = LayerMask.NameToLayer(greenLayerName);

            m_RedLayerMask = LayerMask.GetMask(redLayerName);
            m_RedLayerId = LayerMask.NameToLayer(redLayerName);

            m_YellowLayerMask = LayerMask.GetMask(yellowLayerName);
            m_YellowLayerId = LayerMask.NameToLayer(yellowLayerName);
        }

        public static void Resonate(ResonateColor color)
        {
            Instance.StartCoroutine(Instance.SetupResonate(color));
        }

        protected IEnumerator SetupResonate(ResonateColor color)
        {
            m_TimeRemaining = 1f * m_ResonateTime;
            if (m_CurrentColor == color)
            {
                yield break;
            }
            m_CurrentColor = color;

            int playerLayer = PlayerCharacter.PlayerInstance.gameObject.layer;
            int colorLayerId = GetColorLayerId(color);
            LayerMask colorLayerMask = GetColorLayerMask(color);

            EnableAllCollisions(playerLayer);
            Physics2D.IgnoreLayerCollision(playerLayer, colorLayerId, true);

            ContactFilter2D contactFilter = PlayerCharacter.PlayerInstance.characterController.ContactFilter;
            LayerMask groundedLayerMask = PlayerCharacter.PlayerInstance.characterController.groundedLayerMask;
            contactFilter.layerMask = (groundedLayerMask | colorLayerMask) ^ colorLayerMask;

            if (m_Coroutine != null)
            {
                yield break;
            }
            m_Coroutine = ResonateEffects();
            yield return StartCoroutine(m_Coroutine);

            contactFilter.layerMask = groundedLayerMask;
            EnableAllCollisions(playerLayer);
            m_Coroutine = null;
            m_CurrentColor = ResonateColor.None;
        }

        protected IEnumerator ResonateEffects()
        {
            while (m_TimeRemaining > 0)
            {
                m_TimeRemaining -= Time.deltaTime;
                yield return null;
            }
        }

        protected void EnableAllCollisions(int playerLayer)
        {
            Physics2D.IgnoreLayerCollision(playerLayer, m_BlueLayerId, false);
            Physics2D.IgnoreLayerCollision(playerLayer, m_GreenLayerId, false);
            Physics2D.IgnoreLayerCollision(playerLayer, m_RedLayerId, false);
            Physics2D.IgnoreLayerCollision(playerLayer, m_YellowLayerId, false);
        }

        protected int GetColorLayerId(ResonateColor color)
        {
            switch (color)
            {
                case ResonateColor.Blue:
                    return m_BlueLayerId;
                case ResonateColor.Green:
                    return m_GreenLayerId;
                case ResonateColor.Red:
                    return m_RedLayerId;
                case ResonateColor.Yellow:
                    return m_YellowLayerId;
                default:
                    throw new System.Exception("An unknown color has appeared!");
            }
        }

        protected LayerMask GetColorLayerMask(ResonateColor color)
        {
            switch (color)
            {
                case ResonateColor.Blue:
                    return m_BlueLayerMask;
                case ResonateColor.Green:
                    return m_GreenLayerMask;
                case ResonateColor.Red:
                    return m_RedLayerMask;
                case ResonateColor.Yellow:
                    return m_YellowLayerMask;
                default:
                    throw new System.Exception("An unknown color has appeared!");
            }
        }
    }
}
