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
        bool m_isResonating = false;

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
            Instance.StartCoroutine(Instance.HandleResonate(color));
        }

        protected IEnumerator HandleResonate(ResonateColor color)
        {
            if (!StartResonate(color))
            {
                yield break;
            }

            yield return Resonate();

            StopResonate();
        }

        protected bool StartResonate(ResonateColor color)
        {
            m_TimeRemaining = 1f * m_ResonateTime;
            if (m_CurrentColor == color)
            {
                return false;
            }
            m_CurrentColor = color;

            SetLayerCollisions(color);
            SetContactFilter(color);

            if (m_isResonating)
            {
                return false;
            }
            m_isResonating = true;
            return true;
        }

        protected void StopResonate()
        {
            SetLayerCollisions(ResonateColor.None);
            SetContactFilter(ResonateColor.None);

            m_isResonating = false;
            m_CurrentColor = ResonateColor.None;
        }

        protected IEnumerator Resonate()
        {
            while (m_TimeRemaining > 0)
            {
                m_TimeRemaining -= Time.deltaTime;
                yield return null;
            }
        }

        protected void SetLayerCollisions(ResonateColor color)
        {
            int playerLayer = PlayerCharacter.PlayerInstance.gameObject.layer;

            Physics2D.IgnoreLayerCollision(playerLayer, m_BlueLayerId, color == ResonateColor.Blue);
            Physics2D.IgnoreLayerCollision(playerLayer, m_GreenLayerId, color == ResonateColor.Green);
            Physics2D.IgnoreLayerCollision(playerLayer, m_RedLayerId, color == ResonateColor.Red);
            Physics2D.IgnoreLayerCollision(playerLayer, m_YellowLayerId, color == ResonateColor.Yellow);
        }

        protected void SetContactFilter(ResonateColor color)
        {
            ContactFilter2D contactFilter = PlayerCharacter.PlayerInstance.characterController.ContactFilter;
            LayerMask groundedLayerMask = PlayerCharacter.PlayerInstance.characterController.groundedLayerMask;

            if (color == ResonateColor.None)
            {
                contactFilter.layerMask = groundedLayerMask;
                return;
            }

            LayerMask colorLayerMask = GetColorLayerMask(color);
            contactFilter.layerMask = (groundedLayerMask | colorLayerMask) ^ colorLayerMask;
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
