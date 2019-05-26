using System;
using System.Collections;
using UnityEngine;
using UnityEngine.Rendering.PostProcessing;

namespace Violet
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
        public float resonateTime = 3f;
        public float transitionTime = 0.2f;

        [Tooltip("The Layer with which the character should not collide while phasing blue.")]
        public string blueLayerName;
        public PostProcessVolume blueVolume;
        LayerMask m_BlueLayerMask;
        int m_BlueLayerId;

        [Tooltip("The Layer with which the character should not collide while phasing green.")]
        public string greenLayerName;
        public PostProcessVolume greenVolume;
        LayerMask m_GreenLayerMask;
        int m_GreenLayerId;

        [Tooltip("The Layer with which the character should not collide while phasing red.")]
        public string redLayerName;
        public PostProcessVolume redVolume;
        LayerMask m_RedLayerMask;
        int m_RedLayerId;

        [Tooltip("The Layer with which the character should not collide while phasing yellow.")]
        public string yellowLayerName;
        public PostProcessVolume yellowVolume;
        LayerMask m_YellowLayerMask;
        int m_YellowLayerId;

        ResonateColor m_CurrentColor = ResonateColor.None;
        PostProcessVolume m_ColorVolume;
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

            while (m_TimeRemaining > 0)
            {
                float transitionAmount = Time.deltaTime / transitionTime;
                if (m_TimeRemaining <= transitionTime) {
                    m_ColorVolume.weight -= transitionAmount;
                } else if (m_ColorVolume.weight < 1) {
                    m_ColorVolume.weight = Math.Min(1, m_ColorVolume.weight + transitionAmount);
                }
                if (blueVolume.weight > 0 && m_CurrentColor != ResonateColor.Blue) {
                    blueVolume.weight = Math.Max(0, blueVolume.weight - transitionAmount);
                }
                if (greenVolume.weight > 0 && m_CurrentColor != ResonateColor.Green) {
                    greenVolume.weight = Math.Max(0, greenVolume.weight - transitionAmount);
                }
                if (redVolume.weight > 0 && m_CurrentColor != ResonateColor.Red) {
                    redVolume.weight = Math.Max(0, redVolume.weight - transitionAmount);
                }
                if (yellowVolume.weight > 0 && m_CurrentColor != ResonateColor.Yellow) {
                    yellowVolume.weight = Math.Max(0, yellowVolume.weight - transitionAmount);
                }
                m_TimeRemaining -= Time.deltaTime;
                yield return null;
            }

            StopResonate();
        }

        protected bool StartResonate(ResonateColor color)
        {
            m_TimeRemaining = 1f * resonateTime;
            if (m_CurrentColor == color)
            {
                return false;
            }
            m_CurrentColor = color;
            m_ColorVolume = GetColorVolume(color);

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
            m_ColorVolume.weight = 0;

            m_ColorVolume = null;
            m_CurrentColor = ResonateColor.None;
            m_isResonating = false;
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
            PlayerCharacter playerCharacter = (PlayerCharacter) PlayerCharacter.PlayerInstance;
            LayerMask groundedLayerMask = playerCharacter.characterController.groundedLayerMask;

            if (color == ResonateColor.None)
            {
                playerCharacter.characterController.SetLayerMask(groundedLayerMask);
                return;
            }

            LayerMask colorLayerMask = GetColorLayerMask(color);
            LayerMask filteredLayerMask = (groundedLayerMask | colorLayerMask) ^ colorLayerMask;
            playerCharacter.characterController.SetLayerMask(filteredLayerMask);
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

        protected PostProcessVolume GetColorVolume(ResonateColor color)
        {
            switch (color)
            {
                case ResonateColor.Blue:
                    return blueVolume;
                case ResonateColor.Green:
                    return greenVolume;
                case ResonateColor.Red:
                    return redVolume;
                case ResonateColor.Yellow:
                    return yellowVolume;
                default:
                    throw new System.Exception("An unknown color has appeared!");
            }
        }
    }
}
