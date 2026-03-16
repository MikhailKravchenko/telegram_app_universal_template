import React from 'react';
import {useAuth} from '@/shared/lib';

interface BubbleLoadingProps {
    className?: string;
}

export const BubbleLoading: React.FC<BubbleLoadingProps> = ({className}) => {
    const {isLoading} = useAuth();

    return (
        <div
            className={className}
            style={{
                width: '100vw',
                height: 'calc(100vh - 120px)',
                minHeight: 'calc(100vh - 120px)',
                position: 'relative',
                overflow: 'hidden',
            }}
        >
            <div style={{transform: 'scale(1.5)', width: '100%', height: '100%'}}>
                {/* Static when not loading */}
                {!isLoading && (
                    <svg xmlns="http://www.w3.org/2000/svg" width="100%" height="100%" viewBox="0 0 151 63" fill="none">
                        <path
                            fillRule="evenodd"
                            clipRule="evenodd"
                            d="M44.7607 7.21943C49.9828 -1.80058 63.3012 -0.843837 67.1805 8.82999L79.9197 40.5984L87.5921 23.4567H150.312V39.7067H98.1222L91.1394 55.3077C86.6311 65.38 72.2354 65.0959 68.1282 54.8535L54.9647 22.0271L44.7291 39.7067H0V23.4567H35.3602L44.7607 7.21943Z"
                            fill="#272727"
                        />
                    </svg>
                )}

                {/* Smooth animated gradient when loading */}
                {isLoading && (
                    <svg
                        xmlns="http://www.w3.org/2000/svg"
                        width="100%"
                        height="100%"
                        viewBox="0 0 151 63"
                        fill="none"
                        style={{position: 'absolute', inset: 0, width: '100%', height: '100%'}}
                    >
                        <path
                            fillRule="evenodd"
                            clipRule="evenodd"
                            d="M44.7607 7.21943C49.9828 -1.80058 63.3012 -0.843837 67.1805 8.82999L79.9197 40.5984L87.5921 23.4567H150.312V39.7067H98.1222L91.1394 55.3077C86.6311 65.38 72.2354 65.0959 68.1282 54.8535L54.9647 22.0271L44.7291 39.7067H0V23.4567H35.3602L44.7607 7.21943Z"
                            fill="url(#bubbleGradientAnim)"
                        />
                        <defs>
                            {/**
                             * Animate the gradient smoothly across the shape using SVG SMIL.
                             * We move the gradient along X with animateTransform translating from left to right.
                             */}
                            <linearGradient
                                id="bubbleGradientAnim"
                                x1="0"
                                y1="0"
                                x2="200"
                                y2="0"
                                gradientUnits="userSpaceOnUse"
                                gradientTransform="translate(-120 0)"
                            >
                                <stop stopColor="#272727" />
                                <stop offset="0.471154" stopColor="#8D8D8D" />
                                <stop offset="0.759615" stopColor="#272727" />
                                <animateTransform
                                    attributeName="gradientTransform"
                                    attributeType="XML"
                                    type="translate"
                                    from="-120 0"
                                    to="160 0"
                                    dur="1.5s"
                                    repeatCount="indefinite"
                                    calcMode="linear"
                                />
                            </linearGradient>
                        </defs>
                    </svg>
                )}
            </div>
        </div>
    );
};
